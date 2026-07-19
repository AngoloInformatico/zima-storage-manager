from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from .runner import CommandRunner
from ..models import DiskRecord
from ..constants import SERVICE_CANDIDATES

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")
SUPPORTED_FILESYSTEMS = {"ntfs", "exfat", "vfat", "fat", "fat16", "fat32", "ext2", "ext3", "ext4", "btrfs", "xfs"}
PROTECTED_MOUNTS = {"/", "/boot", "/boot/efi", "/DATA", "/media", "/var/lib/docker", "/var/lib/casaos"}


def validate_name(name: str) -> str:
    name = name.strip()
    if not SAFE_NAME.fullmatch(name) or name in {".", ".."}:
        raise ValueError(
            "Il nome deve contenere da 1 a 64 caratteri: lettere, numeri, spazi, punto, trattino o trattino basso"
        )
    return name


def require_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError("Questa operazione richiede privilegi root")


class SystemInspector:
    def __init__(self, runner: CommandRunner | None = None):
        self.runner = runner or CommandRunner()
        self.host_namespace = os.getenv("ZSM_HOST_NAMESPACE", "0") == "1"

    def _run(self, args: list[str]):
        if self.host_namespace:
            args = ["nsenter", "-t", "1", "-m", "-p", "--", *args]
        return self.runner.run(args)

    def _must_run(self, args: list[str], action: str):
        result = self._run(args)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout or f"Operazione non riuscita: {action}")
        return result

    def lsblk(self) -> list[dict]:
        result = self._run(["lsblk", "-J", "-o", "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS"])
        if result.returncode:
            return []

        def flatten(nodes):
            output = []
            for node in nodes:
                output.append(node)
                output += flatten(node.get("children", []))
            return output

        try:
            return flatten(json.loads(result.stdout).get("blockdevices", []))
        except (json.JSONDecodeError, TypeError):
            return []

    def blocks_by_uuid(self) -> dict[str, dict]:
        return {
            str(item.get("uuid") or "").casefold(): item
            for item in self.lsblk()
            if item.get("uuid")
        }

    def active_mounts(self) -> dict[str, list[str]]:
        result = self._run(["findmnt", "-J", "-o", "SOURCE,TARGET,UUID"])
        if result.returncode:
            return {}
        mounts: dict[str, list[str]] = {}

        def walk(nodes):
            for node in nodes:
                uuid = node.get("uuid") or ""
                target = node.get("target") or ""
                if uuid and target:
                    mounts.setdefault(uuid.casefold(), []).append(target)
                walk(node.get("children", []))

        try:
            walk(json.loads(result.stdout).get("filesystems", []))
        except (json.JSONDecodeError, TypeError):
            return {}
        return mounts

    def enrich(self, records: list[DiskRecord], active_only: bool = False) -> list[DiskRecord]:
        blocks = self.blocks_by_uuid()
        mounts = self.active_mounts()
        output: list[DiskRecord] = []
        for record in records:
            block = blocks.get(record.uuid.casefold())
            if active_only and not block:
                continue
            block = block or {}
            record.label = block.get("label") or ""
            record.device = block.get("path") or ""
            record.fs_type = (block.get("fstype") or "").casefold()
            record.size = block.get("size") or ""
            record.active_mounts = tuple(mounts.get(record.uuid.casefold(), []))
            output.append(record)
        return output

    def get_live_disk(self, record: DiskRecord) -> DiskRecord:
        enriched = self.enrich([record], active_only=True)
        if not enriched:
            raise RuntimeError("Il dispositivo non è attualmente rilevato dal sistema")
        return enriched[0]

    def assert_rename_safe(self, disk: DiskRecord) -> None:
        if not disk.uuid or not disk.device:
            raise RuntimeError("Dispositivo o UUID non disponibile")
        fs = disk.fs_type.casefold()
        if fs not in SUPPORTED_FILESYSTEMS:
            raise RuntimeError(f"Filesystem non supportato: {disk.fs_type or 'sconosciuto'}")
        if disk.device in {"/dev/loop0", "/dev/loop1"} or disk.device.startswith("/dev/loop"):
            raise RuntimeError("I dispositivi di sistema loop non possono essere rinominati")
        for mount in disk.active_mounts:
            normalized = os.path.normpath(mount)
            if normalized in PROTECTED_MOUNTS or normalized.startswith("/var/lib/docker/"):
                raise RuntimeError(f"Volume protetto perché montato su {mount}")

    def unmount_all(self, disk: DiskRecord) -> list[str]:
        mounts = sorted(set(disk.active_mounts), key=len, reverse=True)
        for mount in mounts:
            self._must_run(["umount", mount], f"smontaggio di {mount}")
        return mounts

    def mount_device(self, device: str, target: str) -> None:
        Path(target).mkdir(parents=True, exist_ok=True)
        self._must_run(["mount", device, target], f"montaggio di {device}")

    def remove_empty_mount_dirs(self, paths: list[str]) -> None:
        for value in sorted(set(paths), key=len, reverse=True):
            try:
                path = Path(value)
                if path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
            except (OSError, PermissionError):
                pass

    def label_command(self, disk: DiskRecord, label: str) -> list[str]:
        fs = disk.fs_type.casefold()
        candidates: list[list[str]]
        if fs == "ntfs":
            candidates = [["ntfslabel", disk.device, label]]
        elif fs == "exfat":
            candidates = [["exfatlabel", disk.device, label], ["tune.exfat", "-L", label, disk.device]]
        elif fs in {"vfat", "fat", "fat16", "fat32"}:
            candidates = [["fatlabel", disk.device, label]]
        elif fs in {"ext2", "ext3", "ext4"}:
            candidates = [["e2label", disk.device, label]]
        elif fs == "btrfs":
            candidates = [["btrfs", "filesystem", "label", disk.device, label]]
        elif fs == "xfs":
            candidates = [["xfs_admin", "-L", label, disk.device]]
        else:
            raise RuntimeError(f"Filesystem non supportato: {fs}")

        for command in candidates:
            probe = self._run(["sh", "-c", f"command -v {command[0]}"])
            if probe.returncode == 0:
                return command
        names = " oppure ".join(item[0] for item in candidates)
        raise RuntimeError(f"Comando necessario non disponibile: {names}")

    def set_label(self, disk: DiskRecord, label: str) -> None:
        command = self.label_command(disk, label)
        self._must_run(command, f"modifica etichetta {disk.device}")

    def read_label(self, device: str) -> str:
        result = self._run(["blkid", "-s", "LABEL", "-o", "value", device])
        return result.stdout.strip() if result.returncode == 0 else ""

    def resolve_service(self, service: str) -> str:
        if service and service != "auto":
            return service
        for candidate in SERVICE_CANDIDATES:
            result = self._run(["systemctl", "show", candidate, "--property=LoadState", "--value"])
            if result.returncode == 0 and result.stdout not in {"", "not-found"}:
                return candidate
        return SERVICE_CANDIDATES[0]

    def service_state(self, service: str) -> str:
        resolved = self.resolve_service(service)
        result = self._run(["systemctl", "is-active", resolved])
        return result.stdout or ("unknown" if result.returncode == 127 else "inactive")

    def service(self, action: str, service: str) -> None:
        if action not in {"start", "stop", "restart"}:
            raise ValueError(f"Azione systemd non consentita: {action}")
        resolved = self.resolve_service(service)
        result = self._run(["systemctl", action, resolved])
        if result.returncode:
            raise RuntimeError(result.stderr or f"Impossibile eseguire {action} su {resolved}")

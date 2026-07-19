from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from .runner import CommandRunner
from ..models import DiskRecord
from ..constants import SERVICE_CANDIDATES

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")
SUPPORTED_FILESYSTEMS = {"ntfs", "exfat", "vfat", "fat", "fat16", "fat32", "ext2", "ext3", "ext4", "btrfs", "xfs"}


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

    def _run(self, args: list[str], timeout: int = 30):
        if self.host_namespace:
            args = ["nsenter", "-t", "1", "-m", "-p", "--", *args]
        return self.runner.run(args, timeout=timeout)

    def lsblk(self) -> list[dict]:
        result = self._run(["lsblk", "-J", "-o", "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS"])
        if result.returncode:
            return []

        def flatten(nodes):
            output = []
            for node in nodes:
                output.append(node)
                output += flatten(node.get("children", []) or [])
            return output

        try:
            return flatten(json.loads(result.stdout).get("blockdevices", []))
        except (json.JSONDecodeError, TypeError):
            return []

    def block_by_uuid(self, uuid: str) -> dict | None:
        wanted = uuid.casefold()
        for item in self.lsblk():
            if str(item.get("uuid") or "").casefold() == wanted:
                return item
        return None

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
                walk(node.get("children", []) or [])

        try:
            walk(json.loads(result.stdout).get("filesystems", []))
        except (json.JSONDecodeError, TypeError):
            return {}
        return mounts

    def enrich(self, records: list[DiskRecord], live_only: bool = False) -> list[DiskRecord]:
        blocks = {
            str(item.get("uuid") or "").casefold(): item
            for item in self.lsblk()
            if item.get("uuid")
        }
        mounts = self.active_mounts()
        output: list[DiskRecord] = []
        for record in records:
            block = blocks.get(record.uuid.casefold())
            if live_only and not block:
                continue
            block = block or {}
            record.label = block.get("label") or ""
            record.device = block.get("path") or ""
            record.fs_type = (block.get("fstype") or "").lower()
            record.size = block.get("size") or ""
            record.active_mounts = tuple(mounts.get(record.uuid.casefold(), []))
            output.append(record)
        return output

    def ensure_rename_safe(self, record: DiskRecord) -> None:
        if not record.device:
            raise RuntimeError("Il dispositivo non è attualmente rilevato")
        fs = record.fs_type.lower()
        if fs not in SUPPORTED_FILESYSTEMS:
            raise ValueError(f"Filesystem non supportato per la rinomina: {fs or 'sconosciuto'}")
        protected = {"/", "/boot", "/boot/efi", "/DATA"}
        for mount in record.active_mounts:
            if mount in protected:
                raise PermissionError(f"Volume di sistema protetto: {mount}")

    def mounts_for_device(self, device: str) -> list[str]:
        """Return only mount targets currently backed by *device*.

        The database mount point and lsblk data can be stale after a rename or a
        hot-plug cycle. findmnt is the source of truth immediately before an
        unmount operation.
        """
        result = self._run(["findmnt", "-rn", "-S", device, "-o", "TARGET"])
        if result.returncode not in {0, 1}:
            raise RuntimeError(result.stderr or result.stdout or f"Impossibile leggere i mount di {device}")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def busy_processes(self, mount_point: str) -> str:
        # BusyBox fuser, presente in alcune immagini, non supporta -v. Questo
        # controllo è solo diagnostico e non deve causare un secondo errore.
        result = self._run(["fuser", "-m", mount_point], timeout=15)
        text = "\n".join(x for x in (result.stdout, result.stderr) if x).strip()
        return text

    def unmount_device(self, device: str) -> list[str]:
        """Unmount the real, current targets for a block device.

        A device that is already unmounted is a valid state and returns an empty
        list. Stale database paths are never passed to umount.
        """
        mounts = self.mounts_for_device(device)
        unmounted: list[str] = []
        for mount in sorted(set(mounts), key=len, reverse=True):
            result = self._run(["umount", mount], timeout=30)
            if result.returncode:
                # Re-read the mount table: a concurrent service may already have
                # removed it, in which case the desired state has been reached.
                if mount not in self.mounts_for_device(device):
                    unmounted.append(mount)
                    continue
                busy = self.busy_processes(mount)
                detail = f"\nProcessi che usano il volume:\n{busy}" if busy else ""
                message = (result.stderr or result.stdout or "errore sconosciuto").strip()
                raise RuntimeError(f"Impossibile smontare {mount}: {message}{detail}")
            unmounted.append(mount)

        remaining = self.mounts_for_device(device)
        if remaining:
            raise RuntimeError(
                f"Il dispositivo {device} risulta ancora montato su: {', '.join(remaining)}"
            )
        return unmounted

    def unmount_all(self, mount_points: tuple[str, ...] | list[str]) -> list[str]:
        """Legacy helper retained for API compatibility."""
        unmounted: list[str] = []
        for mount in sorted(set(mount_points), key=len, reverse=True):
            result = self._run(["umount", mount], timeout=30)
            if result.returncode and "not mounted" not in (result.stderr or result.stdout).lower():
                busy = self.busy_processes(mount)
                detail = f"\nProcessi che usano il volume:\n{busy}" if busy else ""
                raise RuntimeError(f"Impossibile smontare {mount}: {result.stderr or result.stdout}{detail}")
            if result.returncode == 0:
                unmounted.append(mount)
        return unmounted

    def _first_available(self, commands: list[str]) -> str:
        for command in commands:
            result = self._run(["sh", "-c", f"command -v {command}"])
            if result.returncode == 0 and result.stdout:
                return command
        raise RuntimeError("Comando necessario non disponibile: " + " oppure ".join(commands))

    def set_filesystem_label(self, device: str, fs_type: str, label: str) -> None:
        fs = fs_type.lower()
        if fs == "ntfs":
            args = [self._first_available(["ntfslabel"]), device, label]
        elif fs == "exfat":
            command = self._first_available(["exfatlabel", "tune.exfat"])
            args = [command, device, label] if command == "exfatlabel" else [command, "-L", label, device]
        elif fs in {"vfat", "fat", "fat16", "fat32"}:
            args = [self._first_available(["fatlabel"]), device, label]
        elif fs in {"ext2", "ext3", "ext4"}:
            args = [self._first_available(["e2label"]), device, label]
        elif fs == "btrfs":
            args = [self._first_available(["btrfs"]), "filesystem", "label", device, label]
        elif fs == "xfs":
            args = [self._first_available(["xfs_admin"]), "-L", label, device]
        else:
            raise ValueError(f"Filesystem non supportato: {fs}")
        result = self._run(args, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout or "Rinomina etichetta non riuscita")

    def settle(self) -> None:
        self._run(["udevadm", "settle"], timeout=30)

    def wait_for_label(self, uuid: str, label: str, timeout: int = 30) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            block = self.block_by_uuid(uuid)
            if block and str(block.get("label") or "") == label:
                return block
            time.sleep(1)
        block = self.block_by_uuid(uuid) or {}
        raise RuntimeError(f"Verifica LABEL fallita: attesa '{label}', rilevata '{block.get('label') or ''}'")

    def wait_for_mount(self, uuid: str, target: str, timeout: int = 35) -> None:
        deadline = time.monotonic() + timeout
        wanted = str(Path(target))
        while time.monotonic() < deadline:
            mounts = self.active_mounts().get(uuid.casefold(), [])
            if wanted in mounts:
                return
            time.sleep(1)
        mounts = self.active_mounts().get(uuid.casefold(), [])
        raise RuntimeError(f"Il volume non è stato rimontato su {target}. Mount attivi: {', '.join(mounts) or 'nessuno'}")

    def remove_empty_old_mount_dirs(self, old_name: str, roots: list[Path]) -> list[str]:
        removed: list[str] = []
        for root in roots:
            candidate = root / old_name
            try:
                if candidate.is_dir() and not any(candidate.iterdir()):
                    candidate.rmdir()
                    removed.append(str(candidate))
            except (OSError, PermissionError):
                continue
        return removed

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
        result = self._run(["systemctl", action, resolved], timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr or f"Impossibile eseguire {action} su {resolved}")

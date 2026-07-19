from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .runner import CommandRunner
from ..models import DiskRecord
from ..constants import SERVICE_CANDIDATES

SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")


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

    def enrich(self, records: list[DiskRecord]) -> list[DiskRecord]:
        blocks = {
            str(item.get("uuid") or "").casefold(): item
            for item in self.lsblk()
            if item.get("uuid")
        }
        mounts = self.active_mounts()
        for record in records:
            block = blocks.get(record.uuid.casefold(), {})
            record.label = block.get("label") or ""
            record.device = block.get("path") or ""
            record.fs_type = block.get("fstype") or ""
            record.size = block.get("size") or ""
            record.active_mounts = tuple(mounts.get(record.uuid.casefold(), []))
        return records

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

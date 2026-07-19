from __future__ import annotations
import json, os, re
from pathlib import Path
from .runner import CommandRunner
from ..models import DiskRecord

SAFE_NAME=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,63}$")

def validate_name(name: str) -> str:
    name=name.strip()
    if not SAFE_NAME.fullmatch(name) or name in {".",".."}: raise ValueError("Name must be 1-64 characters: letters, digits, spaces, dot, underscore or hyphen")
    return name

def require_root() -> None:
    if os.geteuid()!=0: raise PermissionError("This operation requires root privileges. Run with sudo.")

class SystemInspector:
    def __init__(self, runner: CommandRunner | None=None): self.runner=runner or CommandRunner()
    def lsblk(self) -> list[dict]:
        r=self.runner.run(["lsblk","-J","-o","NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS"])
        if r.returncode: return []
        def flat(nodes):
            out=[]
            for n in nodes: out.append(n); out += flat(n.get("children",[]))
            return out
        return flat(json.loads(r.stdout).get("blockdevices",[]))
    def active_mounts(self) -> dict[str,list[str]]:
        r=self.runner.run(["findmnt","-J","-o","SOURCE,TARGET,UUID"])
        if r.returncode: return {}
        result={}
        def walk(nodes):
            for n in nodes:
                uuid=n.get("uuid") or ""; target=n.get("target") or ""
                if uuid and target: result.setdefault(uuid.lower(),[]).append(target)
                walk(n.get("children",[]))
        walk(json.loads(r.stdout).get("filesystems",[])); return result
    def enrich(self, records: list[DiskRecord]) -> list[DiskRecord]:
        blocks={str(x.get("uuid") or "").lower():x for x in self.lsblk() if x.get("uuid")}
        mounts=self.active_mounts()
        for r in records:
            b=blocks.get(r.uuid.lower(),{}); r.label=b.get("label") or ""; r.device=b.get("path") or ""; r.fs_type=b.get("fstype") or ""; r.size=b.get("size") or ""; r.active_mounts=tuple(mounts.get(r.uuid.lower(),[]))
        return records
    def service_state(self, service: str) -> str:
        r=self.runner.run(["systemctl","is-active",service]); return r.stdout or ("unknown" if r.returncode==127 else "inactive")
    def service(self, action: str, service: str) -> None:
        r=self.runner.run(["systemctl",action,service]);
        if r.returncode: raise RuntimeError(r.stderr or f"Unable to {action} {service}")

from dataclasses import dataclass, asdict
from typing import Any

@dataclass(slots=True)
class DiskRecord:
    uuid: str
    mount_point: str
    db_id: int | None = None
    label: str = ""
    device: str = ""
    fs_type: str = ""
    size: str = ""
    active_mounts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["active_mounts"] = list(self.active_mounts)
        return data

@dataclass(slots=True)
class AuditItem:
    code: str
    level: str
    title: str
    detail: str
    recommendation: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

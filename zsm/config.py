from __future__ import annotations
import json, os
from dataclasses import dataclass, field
from pathlib import Path
from .constants import DEFAULT_DB, DEFAULT_SERVICE, DEFAULT_MOUNT_ROOTS

@dataclass(slots=True)
class Config:
    database_path: Path = Path(DEFAULT_DB)
    service_name: str = DEFAULT_SERVICE
    mount_roots: list[Path] = field(default_factory=lambda: [Path(x) for x in DEFAULT_MOUNT_ROOTS])
    backup_dir: Path = Path("/var/lib/zsm/backups")
    report_dir: Path = Path("/var/lib/zsm/reports")
    log_dir: Path = Path("/var/log/zsm")
    stop_service_during_write: bool = True
    theme: str = "dark"

    @classmethod
    def load(cls, explicit: str | None = None) -> "Config":
        candidates = []
        if explicit: candidates.append(Path(explicit))
        if os.getenv("ZSM_CONFIG"): candidates.append(Path(os.environ["ZSM_CONFIG"]))
        candidates += [Path("/etc/zsm/config.json"), Path.home()/".config/zsm/config.json"]
        data = {}
        for path in candidates:
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8")); break
        return cls(
            database_path=Path(data.get("database_path", DEFAULT_DB)),
            service_name=data.get("service_name", DEFAULT_SERVICE),
            mount_roots=[Path(x) for x in data.get("mount_roots", DEFAULT_MOUNT_ROOTS)],
            backup_dir=Path(data.get("backup_dir", "/var/lib/zsm/backups")),
            report_dir=Path(data.get("report_dir", "/var/lib/zsm/reports")),
            log_dir=Path(data.get("log_dir", "/var/log/zsm")),
            stop_service_during_write=bool(data.get("stop_service_during_write", True)),
            theme=data.get("theme", "dark"),
        )

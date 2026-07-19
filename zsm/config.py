from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .constants import DEFAULT_DB, DEFAULT_MOUNT_ROOTS, DEFAULT_SERVICE


@dataclass(slots=True)
class Config:
    database_path: Path = Path(DEFAULT_DB)
    service_name: str = DEFAULT_SERVICE
    mount_roots: list[Path] = field(
        default_factory=lambda: [Path(item) for item in DEFAULT_MOUNT_ROOTS]
    )
    backup_dir: Path = Path("/var/lib/zsm/backups")
    report_dir: Path = Path("/var/lib/zsm/reports")
    log_dir: Path = Path("/var/log/zsm")
    stop_service_during_write: bool = True
    backup_retention: int = 25
    theme: str = "dark"

    @classmethod
    def load(cls, explicit: str | None = None) -> "Config":
        candidates: list[Path] = []
        if explicit:
            candidates.append(Path(explicit))
        if os.getenv("ZSM_CONFIG"):
            candidates.append(Path(os.environ["ZSM_CONFIG"]))
        candidates.extend(
            [Path("/etc/zsm/config.json"), Path.home() / ".config/zsm/config.json"]
        )

        data: dict[str, object] = {}
        for path in candidates:
            if path.is_file():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError) as exc:
                    raise RuntimeError(f"Configurazione non valida: {path}: {exc}") from exc
                if not isinstance(loaded, dict):
                    raise RuntimeError(f"La configurazione deve essere un oggetto JSON: {path}")
                data = loaded
                break

        retention = int(data.get("backup_retention", 25))
        if retention < 1 or retention > 500:
            raise ValueError("backup_retention deve essere compreso tra 1 e 500")

        roots = [Path(str(item)) for item in data.get("mount_roots", DEFAULT_MOUNT_ROOTS)]
        if not roots:
            raise ValueError("mount_roots non può essere vuoto")

        return cls(
            database_path=Path(str(data.get("database_path", DEFAULT_DB))),
            service_name=str(data.get("service_name", DEFAULT_SERVICE)),
            mount_roots=roots,
            backup_dir=Path(str(data.get("backup_dir", "/var/lib/zsm/backups"))),
            report_dir=Path(str(data.get("report_dir", "/var/lib/zsm/reports"))),
            log_dir=Path(str(data.get("log_dir", "/var/log/zsm"))),
            stop_service_during_write=bool(data.get("stop_service_during_write", True)),
            backup_retention=retention,
            theme=str(data.get("theme", "dark")),
        )

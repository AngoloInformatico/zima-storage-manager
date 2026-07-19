from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .constants import DB_CANDIDATES, DEFAULT_DB, DEFAULT_MOUNT_ROOTS, DEFAULT_SERVICE


def _env_bool(name: str, fallback: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return fallback
    return value.strip().casefold() in {"1", "true", "yes", "on"}


def _detect_database(configured: str) -> Path:
    override = os.getenv("ZSM_DATABASE_PATH")
    if override:
        return Path(override)
    path = Path(configured)
    if path.is_file():
        return path
    for candidate in DB_CANDIDATES:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            return candidate_path
    return path


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
    container_mode: bool = False

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

        retention = int(os.getenv("ZSM_BACKUP_RETENTION", str(data.get("backup_retention", 25))))
        if retention < 1 or retention > 500:
            raise ValueError("backup_retention deve essere compreso tra 1 e 500")

        raw_roots = os.getenv("ZSM_MOUNT_ROOTS")
        roots_data = raw_roots.split(":") if raw_roots else data.get("mount_roots", DEFAULT_MOUNT_ROOTS)
        roots = [Path(str(item)) for item in roots_data if str(item)]
        if not roots:
            raise ValueError("mount_roots non può essere vuoto")

        configured_db = str(data.get("database_path", DEFAULT_DB))
        return cls(
            database_path=_detect_database(configured_db),
            service_name=os.getenv("ZSM_SERVICE_NAME", str(data.get("service_name", DEFAULT_SERVICE))),
            mount_roots=roots,
            backup_dir=Path(os.getenv("ZSM_BACKUP_DIR", str(data.get("backup_dir", "/var/lib/zsm/backups")))),
            report_dir=Path(os.getenv("ZSM_REPORT_DIR", str(data.get("report_dir", "/var/lib/zsm/reports")))),
            log_dir=Path(os.getenv("ZSM_LOG_DIR", str(data.get("log_dir", "/var/log/zsm")))),
            stop_service_during_write=_env_bool(
                "ZSM_STOP_SERVICE_DURING_WRITE", bool(data.get("stop_service_during_write", True))
            ),
            backup_retention=retention,
            theme=str(data.get("theme", "dark")),
            container_mode=_env_bool("ZSM_CONTAINER_MODE", False),
        )

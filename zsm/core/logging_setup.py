from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_dir: Path) -> logging.Logger:
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log_dir = Path.home() / ".local/state/zsm/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("zsm")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            log_dir / "zsm.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger

def timeline(log_dir: Path, action: str, status: str, details: dict) -> None:
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        log_dir = Path.home() / ".local/state/zsm/logs"
        log_dir.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "status": status,
        "details": details,
    }
    with (log_dir / "timeline.jsonl").open("a", encoding="utf-8") as file:
        file.write(json.dumps(row, ensure_ascii=False) + "\n")

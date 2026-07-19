from __future__ import annotations

import json
from pathlib import Path


def read_timeline(log_dir: Path, limit: int = 100) -> list[dict]:
    """Read the newest valid timeline entries without failing on corrupt lines."""
    path = log_dir / "timeline.jsonl"
    if not path.is_file():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows[-max(1, limit):][::-1]


def clear_timeline(log_dir: Path) -> bool:
    """Remove the operation timeline safely. Returns True if a file existed."""
    path = log_dir / "timeline.jsonl"
    if not path.exists():
        return False
    if not path.is_file():
        raise ValueError("Il percorso della cronologia non è un file regolare")
    path.unlink()
    return True

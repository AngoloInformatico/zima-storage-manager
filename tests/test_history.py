import json
from pathlib import Path

from zsm.core.history import read_timeline


def test_history_returns_newest_first_and_skips_invalid_lines(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    path = log_dir / "timeline.jsonl"
    path.write_text(
        json.dumps({"timestamp": "1", "action": "backup", "status": "success", "details": {}})
        + "\nnot-json\n"
        + json.dumps({"timestamp": "2", "action": "rename", "status": "success", "details": {}})
        + "\n",
        encoding="utf-8",
    )
    rows = read_timeline(log_dir)
    assert [row["timestamp"] for row in rows] == ["2", "1"]

from zsm.core.history import clear_timeline


def test_clear_timeline_removes_file(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    path = log_dir / "timeline.jsonl"
    path.write_text("{}\n", encoding="utf-8")
    assert clear_timeline(log_dir) is True
    assert not path.exists()
    assert clear_timeline(log_dir) is False

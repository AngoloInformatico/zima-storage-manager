import json
from pathlib import Path

import pytest

from zsm.config import Config


def test_config_loads_backup_retention(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"backup_retention": 12}), encoding="utf-8")
    assert Config.load(str(path)).backup_retention == 12


def test_config_rejects_empty_mount_roots(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"mount_roots": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="mount_roots"):
        Config.load(str(path))

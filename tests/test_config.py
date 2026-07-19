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

def test_environment_overrides(monkeypatch, tmp_path: Path):
    db = tmp_path / "local-storage.db"
    db.write_bytes(b"")
    monkeypatch.setenv("ZSM_DATABASE_PATH", str(db))
    monkeypatch.setenv("ZSM_SERVICE_NAME", "auto")
    monkeypatch.setenv("ZSM_CONTAINER_MODE", "1")
    monkeypatch.setenv("ZSM_MOUNT_ROOTS", "/media:/DATA/.media")
    config = Config.load(str(tmp_path / "missing.json"))
    assert config.database_path == db
    assert config.service_name == "auto"
    assert config.container_mode is True
    assert config.mount_roots == [Path("/media"), Path("/DATA/.media")]

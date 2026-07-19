import sqlite3
from pathlib import Path

import pytest

from zsm.config import Config
from zsm.core.manager import StorageManager


def make_db(path: Path, mount_point: str = "/DATA/.media/NAS2"):
    with sqlite3.connect(path) as con:
        con.execute(
            "CREATE TABLE o_disk (id integer primary key, uuid text, mount_point text, created_at integer, is_deleted integer)"
        )
        con.execute("INSERT INTO o_disk VALUES (1,'ABC',?,0,0)", (mount_point,))


def manager(tmp_path: Path, dry_run: bool = True) -> StorageManager:
    db = tmp_path / "local.db"
    make_db(db)
    cfg = Config(
        database_path=db,
        mount_roots=[tmp_path / "media", Path("/DATA/.media"), Path("/var/lib/casaos_data/.media")],
        backup_dir=tmp_path / "backups",
        report_dir=tmp_path / "reports",
        log_dir=tmp_path / "logs",
        service_name="missing.service",
    )
    return StorageManager(cfg, dry_run=dry_run)


def test_rename_preserves_existing_mount_root(tmp_path):
    result = manager(tmp_path).rename("abc", "NAS3")
    assert result["new"] == "/DATA/.media/NAS3"


def test_rename_rejects_same_name(tmp_path):
    with pytest.raises(ValueError, match="coincide"):
        manager(tmp_path).rename("ABC", "NAS2")


def test_restore_rejects_file_outside_backup_directory(tmp_path):
    instance = manager(tmp_path, dry_run=False)
    outside = tmp_path / "outside.db"
    outside.write_bytes(b"not a database")
    with pytest.raises(ValueError, match="cartella backup"):
        instance.restore(outside)

import sqlite3
from pathlib import Path
from zsm.core.database import StorageDatabase

def make_db(path:Path):
    with sqlite3.connect(path) as c:
        c.execute("CREATE TABLE o_disk (id integer primary key, uuid text, mount_point text, created_at integer, is_deleted integer)")
        c.execute("INSERT INTO o_disk VALUES (1,'ABC','/media/OLD',0,0)")

def test_list_update_backup(tmp_path):
    dbp=tmp_path/"local.db"; make_db(dbp); db=StorageDatabase(dbp)
    assert db.list_records()[0].mount_point=="/media/OLD"
    db.update_mount("abc","/media/NEW"); assert db.get_by_uuid("ABC").mount_point=="/media/NEW"
    assert db.backup(tmp_path/"backups").is_file()

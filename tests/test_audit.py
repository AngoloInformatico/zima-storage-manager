import sqlite3
from zsm.config import Config
from zsm.core.manager import StorageManager
from zsm.core.audit import run_audit

def test_audit_reads_database(tmp_path):
    db=tmp_path/"db.sqlite"
    with sqlite3.connect(db) as c:
        c.execute("CREATE TABLE o_disk (id integer primary key, uuid text, mount_point text, created_at integer, is_deleted integer)")
        c.execute("INSERT INTO o_disk VALUES (1,'MISSING','/media/NAS',0,0)")
    cfg=Config(database_path=db,mount_roots=[tmp_path/"media"],backup_dir=tmp_path/"b",report_dir=tmp_path/"r",log_dir=tmp_path/"l",service_name="missing.service")
    items=run_audit(StorageManager(cfg)); assert any(i.code=="DB_OK" for i in items)

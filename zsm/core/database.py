from __future__ import annotations
import shutil, sqlite3
from datetime import datetime
from pathlib import Path
from ..models import DiskRecord

class StorageDatabase:
    def __init__(self, path: Path): self.path=path
    def validate(self) -> None:
        if not self.path.is_file(): raise FileNotFoundError(f"Database not found: {self.path}")
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as con:
            cols={r[1] for r in con.execute("PRAGMA table_info(o_disk)")}
            required={"id","uuid","mount_point","is_deleted"}
            if not required.issubset(cols): raise RuntimeError(f"Unsupported o_disk schema; missing {required-cols}")
    def list_records(self, include_deleted: bool=False) -> list[DiskRecord]:
        self.validate(); query="SELECT id,uuid,mount_point FROM o_disk"
        if not include_deleted: query += " WHERE COALESCE(is_deleted,0)=0"
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as con:
            return [DiskRecord(db_id=i,uuid=u or "",mount_point=m or "") for i,u,m in con.execute(query)]
    def get_by_uuid(self, uuid: str) -> DiskRecord | None:
        return next((r for r in self.list_records(True) if r.uuid.lower()==uuid.lower()),None)
    def update_mount(self, uuid: str, mount_point: str) -> int:
        self.validate()
        with sqlite3.connect(self.path) as con:
            con.execute("BEGIN IMMEDIATE")
            cur=con.execute("UPDATE o_disk SET mount_point=? WHERE lower(uuid)=lower(?) AND COALESCE(is_deleted,0)=0",(mount_point,uuid))
            if cur.rowcount != 1: con.rollback(); raise RuntimeError(f"Expected one active record for UUID {uuid}, changed {cur.rowcount}")
            con.commit(); return cur.rowcount
    def backup(self, directory: Path) -> Path:
        self.validate(); directory.mkdir(parents=True,exist_ok=True)
        target=directory/f"local-storage-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.db"
        with sqlite3.connect(self.path) as src, sqlite3.connect(target) as dst: src.backup(dst)
        return target
    def restore(self, backup: Path) -> None:
        if not backup.is_file(): raise FileNotFoundError(backup)
        with sqlite3.connect(f"file:{backup}?mode=ro",uri=True) as con: con.execute("PRAGMA quick_check").fetchone()
        temp=self.path.with_suffix(".zsm-restore.tmp")
        shutil.copy2(backup,temp); temp.replace(self.path)

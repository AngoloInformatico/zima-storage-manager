from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from ..models import DiskRecord


class StorageDatabase:
    def __init__(self, path: Path):
        self.path = path

    def validate(self) -> None:
        if not self.path.is_file():
            raise FileNotFoundError(f"Database non trovato: {self.path}")
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as con:
            check = con.execute("PRAGMA quick_check").fetchone()
            if not check or check[0] != "ok":
                raise RuntimeError(f"Controllo integrità SQLite non riuscito: {check}")
            columns = {row[1] for row in con.execute("PRAGMA table_info(o_disk)")}
            required = {"id", "uuid", "mount_point", "is_deleted"}
            if not required.issubset(columns):
                raise RuntimeError(f"Schema o_disk non supportato; colonne mancanti: {required - columns}")

    def list_records(self, include_deleted: bool = False) -> list[DiskRecord]:
        self.validate()
        query = "SELECT id, uuid, mount_point FROM o_disk"
        if not include_deleted:
            query += " WHERE COALESCE(is_deleted, 0)=0"
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as con:
            return [
                DiskRecord(db_id=db_id, uuid=uuid or "", mount_point=mount_point or "")
                for db_id, uuid, mount_point in con.execute(query)
            ]

    def get_by_uuid(self, uuid: str) -> DiskRecord | None:
        matches = [
            record
            for record in self.list_records(True)
            if record.uuid.casefold() == uuid.casefold() and record.uuid
        ]
        if len(matches) > 1:
            active = [record for record in self.list_records(False) if record.uuid.casefold() == uuid.casefold()]
            if len(active) == 1:
                return active[0]
            raise RuntimeError(f"UUID duplicato nel database: {uuid}")
        return matches[0] if matches else None

    def update_mount(self, uuid: str, mount_point: str) -> int:
        self.validate()
        with sqlite3.connect(self.path, timeout=30) as con:
            con.execute("PRAGMA busy_timeout=30000")
            con.execute("BEGIN IMMEDIATE")
            cursor = con.execute(
                "UPDATE o_disk SET mount_point=? "
                "WHERE lower(uuid)=lower(?) AND COALESCE(is_deleted,0)=0",
                (mount_point, uuid),
            )
            if cursor.rowcount != 1:
                con.rollback()
                raise RuntimeError(
                    f"Era atteso un solo record attivo per UUID {uuid}; modificati: {cursor.rowcount}"
                )
            con.commit()
            return cursor.rowcount

    def delete_by_uuid(self, uuid: str) -> int:
        self.validate()
        with sqlite3.connect(self.path, timeout=30) as con:
            con.execute("PRAGMA busy_timeout=30000")
            con.execute("BEGIN IMMEDIATE")
            cursor = con.execute(
                "DELETE FROM o_disk WHERE lower(uuid)=lower(?)", (uuid,)
            )
            if cursor.rowcount != 1:
                con.rollback()
                raise RuntimeError(f"Era atteso un solo record per UUID {uuid}; eliminati: {cursor.rowcount}")
            con.commit()
            return cursor.rowcount

    def backup(self, directory: Path) -> Path:
        self.validate()
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"local-storage-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.db"
        with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as source:
            with sqlite3.connect(target) as destination:
                source.backup(destination)
                result = destination.execute("PRAGMA quick_check").fetchone()
                if not result or result[0] != "ok":
                    raise RuntimeError("Il backup SQLite non ha superato il controllo di integrità")
        shutil.copymode(self.path, target)
        return target

    def restore(self, backup: Path) -> None:
        if not backup.is_file():
            raise FileNotFoundError(backup)
        with sqlite3.connect(f"file:{backup}?mode=ro", uri=True) as con:
            result = con.execute("PRAGMA quick_check").fetchone()
            if not result or result[0] != "ok":
                raise RuntimeError("Il file di backup non è un database SQLite integro")

        stat = self.path.stat()
        temp = self.path.parent / f".{self.path.name}.zsm-restore-{os.getpid()}.tmp"
        shutil.copy2(backup, temp)
        os.chown(temp, stat.st_uid, stat.st_gid)
        os.chmod(temp, stat.st_mode)
        temp.replace(self.path)

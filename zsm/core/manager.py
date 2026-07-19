from __future__ import annotations
from pathlib import Path
from .database import StorageDatabase
from .logging_setup import setup_logging, timeline
from .system import SystemInspector, require_root, validate_name
from ..config import Config

class StorageManager:
    def __init__(self, config: Config, dry_run: bool=False):
        self.config=config; self.dry_run=dry_run; self.db=StorageDatabase(config.database_path); self.system=SystemInspector(); self.log=setup_logging(config.log_dir)
    def disks(self): return self.system.enrich(self.db.list_records())
    def rename(self, uuid: str, name: str) -> dict:
        name=validate_name(name); target=str(self.config.mount_roots[0]/name)
        rec=self.db.get_by_uuid(uuid)
        if not rec: raise LookupError(f"UUID not found: {uuid}")
        if any(r.mount_point==target and r.uuid.lower()!=uuid.lower() for r in self.db.list_records()): raise ValueError(f"Mount point already assigned: {target}")
        if Path(target).exists() and Path(target).is_dir() and any(Path(target).iterdir()): raise ValueError(f"Target directory is not empty: {target}")
        result={"uuid":uuid,"old":rec.mount_point,"new":target,"dry_run":self.dry_run}
        if self.dry_run: timeline(self.config.log_dir,"rename","dry-run",result); return result
        require_root(); backup=self.db.backup(self.config.backup_dir); stopped=False
        try:
            if self.config.stop_service_during_write:
                self.system.service("stop",self.config.service_name); stopped=True
            self.db.update_mount(uuid,target)
            if stopped: self.system.service("start",self.config.service_name); stopped=False
            verify=self.db.get_by_uuid(uuid)
            if not verify or verify.mount_point!=target: raise RuntimeError("Post-write verification failed")
            result["backup"]=str(backup); timeline(self.config.log_dir,"rename","success",result); return result
        except Exception:
            try: self.db.restore(backup)
            finally:
                if stopped:
                    try: self.system.service("start",self.config.service_name)
                    except Exception: pass
            timeline(self.config.log_dir,"rename","rolled-back",result); raise
    def backups(self) -> list[Path]:
        return sorted(self.config.backup_dir.glob("local-storage-*.db"),reverse=True) if self.config.backup_dir.exists() else []
    def create_backup(self) -> Path:
        if not self.dry_run: require_root()
        if self.dry_run: return self.config.backup_dir/"dry-run-backup.db"
        path=self.db.backup(self.config.backup_dir); timeline(self.config.log_dir,"backup","success",{"path":str(path)}); return path
    def restore(self, path: Path) -> None:
        require_root(); safety=self.db.backup(self.config.backup_dir); stopped=False
        try:
            self.system.service("stop",self.config.service_name); stopped=True; self.db.restore(path); self.db.validate(); self.system.service("start",self.config.service_name); stopped=False
            timeline(self.config.log_dir,"restore","success",{"source":str(path),"safety":str(safety)})
        except Exception:
            self.db.restore(safety)
            if stopped:
                try:self.system.service("start",self.config.service_name)
                except Exception:pass
            raise

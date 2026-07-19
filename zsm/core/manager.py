from __future__ import annotations

import threading
from pathlib import Path

from .database import StorageDatabase
from .history import read_timeline
from .logging_setup import setup_logging, timeline
from .system import SystemInspector, require_root, validate_name
from ..config import Config


class StorageManager:
    """Coordinates safe reads and writes to ZimaOS local-storage metadata."""

    _write_lock = threading.RLock()

    def __init__(self, config: Config, dry_run: bool = False):
        self.config = config
        self.dry_run = dry_run
        self.db = StorageDatabase(config.database_path)
        self.system = SystemInspector()
        self.log = setup_logging(config.log_dir)

    def disks(self):
        """Return only records whose UUID is physically present now."""
        return self.system.enrich(self.db.list_records(), active_only=True)

    def stale_records(self):
        live = set(self.system.blocks_by_uuid())
        return [r for r in self.db.list_records() if r.uuid.casefold() not in live]

    def _target_for(self, record, name: str) -> Path:
        current = Path(record.mount_point) if record.mount_point else None
        if current and current.parent != Path(".") and any(current.parent == root for root in self.config.mount_roots):
            return current.parent / name
        return self.config.mount_roots[0] / name

    def rename(self, uuid: str, name: str) -> dict:
        name = validate_name(name)
        with self._write_lock:
            record = self.db.get_by_uuid(uuid)
            if not record:
                raise LookupError(f"UUID non trovato: {uuid}")
            disk = self.system.get_live_disk(record)
            self.system.assert_rename_safe(disk)

            target_path = self._target_for(record, name)
            target = str(target_path)
            if name == disk.label and target == record.mount_point:
                raise ValueError("Il nuovo nome coincide con quello attuale")

            if any(item.mount_point.casefold() == target.casefold() and item.uuid.casefold() != uuid.casefold()
                   for item in self.db.list_records()):
                raise ValueError(f"Nome già utilizzato da un altro disco: {name}")

            for root in self.config.mount_roots:
                candidate = root / name
                if str(candidate) in disk.active_mounts:
                    continue
                if candidate.exists() and candidate.is_dir() and any(candidate.iterdir()):
                    raise ValueError(f"La cartella di destinazione non è vuota: {candidate}")

            result = {"uuid": uuid, "device": disk.device, "filesystem": disk.fs_type,
                      "old_label": disk.label, "new_label": name, "old": record.mount_point,
                      "new": target, "dry_run": self.dry_run}
            if self.dry_run:
                timeline(self.config.log_dir, "rename", "dry-run", result)
                return result

            require_root()
            backup = self.db.backup(self.config.backup_dir)
            old_mounts = list(disk.active_mounts)
            stopped = False
            label_changed = False
            try:
                if self.config.stop_service_during_write:
                    self.system.service("stop", self.config.service_name)
                    stopped = True

                self.system.unmount_all(disk)
                self.system.set_label(disk, name)
                label_changed = True
                actual_label = self.system.read_label(disk.device)
                if actual_label != name:
                    raise RuntimeError(f"Verifica LABEL fallita: attesa '{name}', rilevata '{actual_label}'")

                self.db.update_mount(uuid, target)
                verify = self.db.get_by_uuid(uuid)
                if not verify or verify.mount_point != target:
                    raise RuntimeError("Verifica del database successiva alla scrittura non riuscita")

                self.system.mount_device(disk.device, target)
                self.system.remove_empty_mount_dirs([p for p in old_mounts if p != target])

                if stopped:
                    self.system.service("start", self.config.service_name)
                    stopped = False

                final = self.system.get_live_disk(self.db.get_by_uuid(uuid))
                if final.label != name:
                    raise RuntimeError("La LABEL finale non coincide con il nuovo nome")
                if target not in final.active_mounts:
                    raise RuntimeError(f"Il volume non risulta montato nel nuovo percorso {target}")

                result["backup"] = str(backup)
                self._prune_backups()
                timeline(self.config.log_dir, "rename", "success", result)
                return result
            except Exception:
                try:
                    try:
                        refreshed = self.system.get_live_disk(record)
                        self.system.unmount_all(refreshed)
                    except Exception:
                        pass
                    if label_changed and disk.label:
                        try:
                            self.system.set_label(disk, disk.label)
                        except Exception:
                            pass
                    self.db.restore(backup)
                    if old_mounts:
                        try:
                            self.system.mount_device(disk.device, old_mounts[0])
                        except Exception:
                            pass
                finally:
                    if stopped:
                        try: self.system.service("start", self.config.service_name)
                        except Exception: pass
                timeline(self.config.log_dir, "rename", "rolled-back", result)
                raise

    def history(self, limit: int = 100) -> list[dict]:
        return read_timeline(self.config.log_dir, limit)

    def diagnostics(self) -> dict:
        database_ok = False; database_error = ""
        try: self.db.validate(); database_ok = True
        except Exception as exc: database_error = str(exc)
        resolved_service = self.system.resolve_service(self.config.service_name)
        return {"database": str(self.config.database_path), "database_ok": database_ok,
                "database_error": database_error, "service": self.system.service_state(resolved_service),
                "service_name": resolved_service, "service_configured": self.config.service_name,
                "container_mode": self.config.container_mode, "host_namespace": self.system.host_namespace,
                "mount_roots": [str(root) for root in self.config.mount_roots],
                "backup_dir": str(self.config.backup_dir), "backup_count": len(self.backups()),
                "stale_count": len(self.stale_records()), "dry_run": self.dry_run}

    def backups(self) -> list[Path]:
        if not self.config.backup_dir.exists(): return []
        return sorted(self.config.backup_dir.glob("local-storage-*.db"), reverse=True)

    def _prune_backups(self) -> None:
        for old in self.backups()[self.config.backup_retention:]:
            try: old.unlink()
            except OSError as exc: self.log.warning("Impossibile eliminare il vecchio backup %s: %s", old, exc)

    def create_backup(self) -> Path:
        if not self.dry_run: require_root()
        if self.dry_run: return self.config.backup_dir / "dry-run-backup.db"
        path = self.db.backup(self.config.backup_dir)
        timeline(self.config.log_dir, "backup", "success", {"path": str(path)})
        self._prune_backups(); return path

    def restore(self, path: Path) -> None:
        path = path.resolve(); backup_root = self.config.backup_dir.resolve()
        if path.parent != backup_root or not path.name.startswith("local-storage-") or path.suffix != ".db":
            raise ValueError("Il file selezionato non appartiene alla cartella backup di ZSM")
        require_root()
        with self._write_lock:
            safety = self.db.backup(self.config.backup_dir); stopped = False
            try:
                if self.config.stop_service_during_write:
                    self.system.service("stop", self.config.service_name); stopped = True
                self.db.restore(path); self.db.validate()
                if stopped: self.system.service("start", self.config.service_name); stopped = False
                timeline(self.config.log_dir, "restore", "success", {"source": str(path), "safety": str(safety)})
            except Exception:
                self.db.restore(safety)
                if stopped:
                    try: self.system.service("start", self.config.service_name)
                    except Exception: pass
                raise

from __future__ import annotations

import threading
from pathlib import Path

from .database import StorageDatabase
from .history import clear_timeline, read_timeline
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
        # La schermata principale mostra solo UUID realmente presenti. I record
        # storici del database non devono riapparire come dispositivi fantasma.
        return self.system.enrich(self.db.list_records(), live_only=True)

    def _target_for(self, record, name: str) -> Path:
        """Preserve the record's existing mount root instead of forcing /media."""
        current = Path(record.mount_point) if record.mount_point else None
        if current and current.parent != Path("."):
            parent = current.parent
            allowed = any(parent == root for root in self.config.mount_roots)
            if allowed:
                return parent / name
        return self.config.mount_roots[0] / name

    def rename(self, uuid: str, name: str) -> dict:
        name = validate_name(name)
        with self._write_lock:
            record = self.db.get_by_uuid(uuid)
            if not record:
                raise LookupError(f"UUID non trovato: {uuid}")

            enriched = self.system.enrich([record], live_only=True)
            if not enriched:
                raise RuntimeError("Il dispositivo non è attualmente rilevato")
            record = enriched[0]
            self.system.ensure_rename_safe(record)

            target_path = self._target_for(record, name)
            target = str(target_path)
            old_label = record.label or self.system.read_filesystem_label(record.device)
            old_name = Path(record.mount_point).name
            old_target = record.mount_point
            if target == old_target and old_label == name:
                raise ValueError("Il nuovo nome coincide con quello attuale")

            records = self.db.list_records()
            target_key = target.casefold()
            if any(item.mount_point.casefold() == target_key and item.uuid.casefold() != uuid.casefold() for item in records):
                raise ValueError(f"Nome già utilizzato da un altro disco: {name}")

            for root in self.config.mount_roots:
                candidate = root / name
                if candidate.exists() and candidate.is_dir():
                    try:
                        if any(candidate.iterdir()):
                            raise ValueError(f"La cartella di destinazione non è vuota: {candidate}")
                    except PermissionError as exc:
                        raise PermissionError(f"Impossibile verificare la cartella: {candidate}") from exc

            result = {
                "uuid": uuid, "device": record.device, "filesystem": record.fs_type,
                "old": old_target, "new": target, "old_label": old_label,
                "new_label": name, "mounts_before": list(record.active_mounts),
                "dry_run": self.dry_run,
            }
            if self.dry_run:
                timeline(self.config.log_dir, "rename", "dry-run", result)
                return result

            require_root()
            backup = self.db.backup(self.config.backup_dir)
            stopped = False
            label_changed = False
            mounted_new = False
            try:
                if self.config.stop_service_during_write:
                    self.system.service("stop", self.config.service_name)
                    stopped = True

                result["mounts_detected_before_unmount"] = self.system.mounts_for_device(record.device)
                result["unmounted"] = self.system.unmount_device(record.device)
                self.system.set_filesystem_label(record.device, record.fs_type, name)
                label_changed = True
                self.system.refresh_block_metadata(record.device)
                self.system.wait_for_label(uuid, name, device=record.device)

                self.db.update_mount(uuid, target)
                verify = self.db.get_by_uuid(uuid)
                if not verify or verify.mount_point != target:
                    raise RuntimeError("Verifica successiva alla scrittura del database non riuscita")

                # Il servizio ZimaOS non rimonta sempre un volume già noto dopo il
                # cambio LABEL. Lo montiamo esplicitamente sul nuovo target e solo
                # dopo riavviamo Local Storage, che così adotta lo stato coerente.
                self.system.mount_device(record.device, target)
                mounted_new = True

                if stopped:
                    self.system.service("start", self.config.service_name)
                    stopped = False
                self.system.refresh_block_metadata(record.device)
                self.system.wait_for_mount(uuid, target)

                final_db = self.db.get_by_uuid(uuid)
                if not final_db or final_db.mount_point != target:
                    raise RuntimeError("Il servizio ZimaOS ha ripristinato un mountpoint precedente")
                result["final_state"] = self.system.verify_final_state(
                    uuid, record.device, name, target
                )
                result["removed_old_directories"] = self.system.remove_empty_old_mount_dirs(
                    old_name, self.config.mount_roots
                )
                result["backup"] = str(backup)
                self._prune_backups()
                timeline(self.config.log_dir, "rename", "success", result)
                return result
            except Exception as exc:
                result["error"] = str(exc)
                try:
                    # Libera l'eventuale nuovo mount prima di ripristinare LABEL e DB.
                    if mounted_new:
                        try:
                            self.system.unmount_device(record.device)
                        except Exception as rollback_exc:
                            result["unmount_rollback_error"] = str(rollback_exc)
                    self.db.restore(backup)
                    if label_changed and old_label:
                        try:
                            self.system.set_filesystem_label(record.device, record.fs_type, old_label)
                            self.system.refresh_block_metadata(record.device)
                            self.system.wait_for_label(uuid, old_label, device=record.device)
                        except Exception as rollback_exc:
                            result["label_rollback_error"] = str(rollback_exc)
                    if old_target:
                        try:
                            self.system.mount_device(record.device, old_target)
                        except Exception as rollback_exc:
                            result["mount_rollback_error"] = str(rollback_exc)
                finally:
                    if stopped:
                        try:
                            self.system.service("start", self.config.service_name)
                        except Exception as rollback_exc:
                            result["service_rollback_error"] = str(rollback_exc)
                timeline(self.config.log_dir, "rename", "rolled-back", result)
                raise

    def history(self, limit: int = 100) -> list[dict]:
        return read_timeline(self.config.log_dir, limit)

    def delete_backup(self, name: str) -> None:
        safe_name = Path(name).name
        if not safe_name or safe_name != name or not safe_name.startswith("local-storage-") or not safe_name.endswith(".db"):
            raise ValueError("Nome backup non valido")
        path = (self.config.backup_dir / safe_name).resolve()
        if path.parent != self.config.backup_dir.resolve():
            raise ValueError("Il backup non appartiene alla cartella gestita")
        if not path.is_file():
            raise FileNotFoundError("Backup non trovato")
        require_root()
        path.unlink()
        timeline(self.config.log_dir, "backup-delete", "success", {"path": str(path)})

    def delete_all_backups(self) -> int:
        require_root()
        deleted = 0
        for path in self.backups():
            path.unlink()
            deleted += 1
        timeline(self.config.log_dir, "backup-delete-all", "success", {"count": deleted})
        return deleted

    def clear_history(self) -> bool:
        require_root()
        return clear_timeline(self.config.log_dir)

    def diagnostics(self) -> dict:
        database_ok = False
        database_error = ""
        try:
            self.db.validate()
            database_ok = True
        except Exception as exc:
            database_error = str(exc)
        resolved_service = self.system.resolve_service(self.config.service_name)
        return {
            "database": str(self.config.database_path),
            "database_ok": database_ok,
            "database_error": database_error,
            "service": self.system.service_state(resolved_service),
            "service_name": resolved_service,
            "service_configured": self.config.service_name,
            "container_mode": self.config.container_mode,
            "host_namespace": self.system.host_namespace,
            "mount_roots": [str(root) for root in self.config.mount_roots],
            "backup_dir": str(self.config.backup_dir),
            "backup_count": len(self.backups()),
            "dry_run": self.dry_run,
        }

    def backups(self) -> list[Path]:
        if not self.config.backup_dir.exists():
            return []
        return sorted(self.config.backup_dir.glob("local-storage-*.db"), reverse=True)

    def _prune_backups(self) -> None:
        backups = self.backups()
        for old in backups[self.config.backup_retention :]:
            try:
                old.unlink()
            except OSError as exc:
                self.log.warning("Impossibile eliminare il vecchio backup %s: %s", old, exc)

    def create_backup(self) -> Path:
        if not self.dry_run:
            require_root()
        if self.dry_run:
            return self.config.backup_dir / "dry-run-backup.db"
        path = self.db.backup(self.config.backup_dir)
        timeline(self.config.log_dir, "backup", "success", {"path": str(path)})
        self._prune_backups()
        return path

    def restore(self, path: Path) -> None:
        path = path.resolve()
        backup_root = self.config.backup_dir.resolve()
        if path.parent != backup_root or not path.name.startswith("local-storage-") or path.suffix != ".db":
            raise ValueError("Il file selezionato non appartiene alla cartella backup di ZSM")
        require_root()
        with self._write_lock:
            safety = self.db.backup(self.config.backup_dir)
            stopped = False
            try:
                if self.config.stop_service_during_write:
                    self.system.service("stop", self.config.service_name)
                    stopped = True
                self.db.restore(path)
                self.db.validate()
                if stopped:
                    self.system.service("start", self.config.service_name)
                    stopped = False
                timeline(
                    self.config.log_dir,
                    "restore",
                    "success",
                    {"source": str(path), "safety": str(safety)},
                )
            except Exception:
                self.db.restore(safety)
                if stopped:
                    try:
                        self.system.service("start", self.config.service_name)
                    except Exception:
                        pass
                raise

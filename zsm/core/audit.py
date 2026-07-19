from __future__ import annotations
from collections import Counter
from pathlib import Path
from ..models import AuditItem
from .manager import StorageManager

def run_audit(m: StorageManager) -> list[AuditItem]:
    items=[]
    try: records=m.disks(); items.append(AuditItem("DB_OK","ok","Database readable",f"{len(records)} active disk records"))
    except Exception as e: return [AuditItem("DB_ERROR","error","Database unavailable",str(e),"Verify configuration and permissions")]
    state=m.system.service_state(m.config.service_name)
    items.append(AuditItem("SERVICE", "ok" if state=="active" else "warning", "Local-storage service", state, "Start the service" if state!="active" else ""))
    uuids=[r.uuid.lower() for r in records if r.uuid]
    for u,n in Counter(uuids).items():
        if n>1: items.append(AuditItem("DUP_UUID","error","Duplicate UUID",f"{u}: {n} active records","Remove or deactivate duplicate records manually after backup"))
    points=[r.mount_point for r in records if r.mount_point]
    for p,n in Counter(points).items():
        if n>1: items.append(AuditItem("DUP_MOUNT","error","Duplicate mount point",f"{p}: {n} records","Assign unique mount points"))
    for r in records:
        if not r.uuid: items.append(AuditItem("EMPTY_UUID","error","Missing UUID",f"Record {r.db_id}","Inspect the database record"))
        if not r.device: items.append(AuditItem("DEVICE_MISSING","warning",f"Device not connected: {r.uuid}",r.mount_point,"Reconnect the disk or mark stale metadata"))
        if r.active_mounts and r.mount_point not in r.active_mounts: items.append(AuditItem("MOUNT_MISMATCH","warning",f"Mount mismatch: {r.label or r.uuid}",f"DB={r.mount_point}; active={', '.join(r.active_mounts)}","Restart local-storage after confirming the database value"))
    known={Path(p).resolve() for p in points if p}
    for root in m.config.mount_roots:
        if root.is_dir():
            for d in root.iterdir():
                if d.is_dir() and d.resolve() not in known:
                    items.append(AuditItem("ORPHAN_DIR","info","Unregistered mount directory",str(d),"Verify it is unused before removal"))
    if not any(i.level in {"error","warning"} for i in items): items.append(AuditItem("SUMMARY","ok","Audit passed","No critical inconsistencies detected"))
    return items

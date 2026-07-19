from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import __version__
from .config import Config
from .core.audit import run_audit
from .core.manager import StorageManager
from .reports.generator import write_reports

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zsm", description="ZimaOS storage administration toolkit")
    p.add_argument("--config")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("disks")
    audit = sub.add_parser("audit")
    audit.add_argument("--no-report", action="store_true")
    rename = sub.add_parser("rename")
    rename.add_argument("--uuid", required=True)
    rename.add_argument("--name", required=True)
    sub.add_parser("backup")
    sub.add_parser("backups")
    restore = sub.add_parser("restore")
    restore.add_argument("path", type=Path)
    return p

def main(argv=None) -> int:
    args = parser().parse_args(argv)
    config = Config.load(args.config)
    manager = StorageManager(config, args.dry_run)
    try:
        if args.cmd == "status":
            print(json.dumps({
                "database": str(config.database_path),
                "service": manager.system.service_state(config.service_name),
                "dry_run": args.dry_run,
            }, indent=2))
        elif args.cmd == "disks":
            print(json.dumps([disk.to_dict() for disk in manager.disks()], indent=2))
        elif args.cmd == "rename":
            print(json.dumps(manager.rename(args.uuid, args.name), indent=2))
        elif args.cmd == "backup":
            print(manager.create_backup())
        elif args.cmd == "backups":
            print("\n".join(map(str, manager.backups())))
        elif args.cmd == "restore":
            manager.restore(args.path)
            print("Restore completed")
        elif args.cmd == "audit":
            items = run_audit(manager)
            print("\n".join(f"[{i.level.upper()}] {i.title}: {i.detail}" for i in items))
            if not args.no_report:
                paths = write_reports(items, config.report_dir)
                print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))
            return 2 if any(item.level == "error" for item in items) else 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

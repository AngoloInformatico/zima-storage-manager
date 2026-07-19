# Zima Storage Manager (ZSM)

ZSM is a defensive administration toolkit for inspecting and repairing ZimaOS local-storage metadata. It provides a modern CustomTkinter GUI and an SSH-friendly CLI.

> **Important:** ZSM is an independent community project. It is not affiliated with or endorsed by IceWhale Technology. Always maintain independent backups of important data.

## Features

- Modern dark/light GUI with uniform navigation buttons and hover effects.
- Disk inventory from `lsblk`, database records and active mounts.
- Safe mount-point rename workflow with validation, automatic snapshot and rollback.
- Audit of database, service, mount directories, duplicate mount points and UUID coherence.
- Database backup, listing and restore.
- Diagnostic reports in HTML, Markdown and JSON.
- Operation timeline and rotating logs.
- CLI and GUI `dry-run` mode.
- Configurable paths and service name.

## Supported baseline

The defaults target the ZimaOS/CasaOS local-storage layout observed on ZimaOS 1.6.x:

- Database: `/var/lib/casaos/db/local-storage.db`
- Service: `zimaos-local-storage.service`
- Mount root: `/media`

All values can be overridden in `/etc/zsm/config.json` or `~/.config/zsm/config.json`.

## Quick installation

```bash
chmod +x install.sh
sudo ./install.sh
```

Launch:

```bash
zsm-gui
# or
zsm status
zsm audit
```

For a desktop GUI displayed remotely, an X11/Wayland session is required. SSH-only servers can use the CLI.

## Safe rename example

```bash
sudo zsm rename --uuid 5ECC3C1BCC3BEC41 --name NAS3 --dry-run
sudo zsm rename --uuid 5ECC3C1BCC3BEC41 --name NAS3
```

ZSM changes only the local-storage database mount-point record. It does **not** rename the filesystem label. The service is stopped before the transaction and restarted afterward. A snapshot is always created before a real change.

## Repository layout

- `zsm/`: application source
- `tests/`: automated tests
- `docs/`: installation, usage, architecture and troubleshooting
- `.github/workflows/`: CI validation

## Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
```

## License

MIT. See [LICENSE](LICENSE).

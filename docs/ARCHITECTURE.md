# Architecture

ZSM separates presentation from privileged logic:

- `config.py`: safe JSON configuration with system and user fallbacks.
- `core/database.py`: parameterized SQLite access, schema validation, online backup and atomic restore.
- `core/system.py`: command execution without a shell, device/mount inspection and service control.
- `core/manager.py`: transactional workflows, snapshots and rollback.
- `core/audit.py`: read-only consistency checks.
- `reports/generator.py`: offline HTML, Markdown and JSON reports.
- `gui/`: CustomTkinter presentation.
- `cli.py`: automation and SSH interface.

The GUI never writes SQLite directly. All changes pass through `StorageManager`.

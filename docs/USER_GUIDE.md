# User Guide

## GUI

Run `zsm-gui`. The left navigation uses identical button dimensions, spacing, typography and hover behavior. The active section remains highlighted.

The Rename page defaults to simulation. Enter the filesystem UUID and desired mount directory name, run the simulation, review the result, then disable simulation and rerun with root privileges.

## CLI

- `zsm status`: paths and service state
- `zsm disks`: merged database/device/mount inventory as JSON
- `zsm audit`: checks and creates HTML, Markdown and JSON reports
- `sudo zsm backup`: snapshot the database
- `sudo zsm rename --uuid UUID --name NAME`: change the stored mount point
- `zsm backups`: list snapshots
- `sudo zsm restore PATH`: restore a snapshot

Global flags `--config PATH` and `--dry-run` must precede the subcommand.

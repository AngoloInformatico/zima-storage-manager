# Troubleshooting

## Database not found

Run `zsm status`, then verify `database_path` in `/etc/zsm/config.json`.

## Read-only database

Real changes require `sudo`. Also verify filesystem state and database directory permissions.

## Service name differs

Discover it with `systemctl list-units '*local-storage*'` and update `service_name`.

## GUI does not open

A graphical session and Tk are required. Use the CLI on SSH-only systems.

## Disk remains on the old mount after rename

Safely eject the disk or reboot after confirming the database record. Do not forcibly unmount a busy disk without identifying processes that use it.

## Rollback

Every real rename and restore creates a timestamped safety copy in `backup_dir`. Use `zsm backups` and `sudo zsm restore PATH`.

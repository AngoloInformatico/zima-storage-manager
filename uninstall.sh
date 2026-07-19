#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then echo "Run with sudo" >&2; exit 1; fi
rm -f /usr/local/bin/zsm /usr/local/bin/zsm-gui /usr/share/applications/zsm.desktop
rm -rf /opt/zima-storage-manager
echo "Application removed. Configuration, backups, reports and logs were preserved."

#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Esegui con sudo: sudo bash uninstall.sh" >&2
  exit 1
fi
systemctl disable --now zima-storage-manager.service 2>/dev/null || true
rm -f /etc/systemd/system/zima-storage-manager.service
systemctl daemon-reload
rm -f /usr/local/bin/zsm /usr/local/bin/zsm-web /usr/local/bin/zsm-gui
rm -rf /opt/zima-storage-manager
echo "Zima Storage Manager rimosso."
echo "Backup e configurazione sono stati conservati in /var/lib/zsm e /etc/zsm."

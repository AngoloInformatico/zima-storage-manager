#!/usr/bin/env bash
set -euo pipefail

[[ ${EUID:-$(id -u)} -eq 0 ]] || {
  echo "Esegui con sudo: sudo bash uninstall.sh" >&2
  exit 1
}

echo "Rimozione di Zima Storage Manager..."
systemctl disable --now zima-storage-manager.service 2>/dev/null || true
rm -f /etc/systemd/system/zima-storage-manager.service
systemctl daemon-reload
rm -f /usr/local/bin/zsm /usr/local/bin/zsm-web /usr/local/bin/zsm-gui /usr/local/bin/zsm-update
rm -rf /opt/zima-storage-manager

echo
echo "Zima Storage Manager è stato rimosso."
echo "Per sicurezza, backup e configurazione sono rimasti in:"
echo "  /var/lib/zsm"
echo "  /etc/zsm"

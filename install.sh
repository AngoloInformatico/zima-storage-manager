#!/usr/bin/env bash
set -euo pipefail
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then echo "Run with sudo: sudo ./install.sh" >&2; exit 1; fi
PYTHON=${PYTHON:-python3}
command -v "$PYTHON" >/dev/null || { echo "python3 is required" >&2; exit 1; }
PREFIX=${PREFIX:-/opt/zima-storage-manager}
VENV="$PREFIX/.venv"
mkdir -p "$PREFIX"
cp -a . "$PREFIX/source"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install "$PREFIX/source"
ln -sf "$VENV/bin/zsm" /usr/local/bin/zsm
ln -sf "$VENV/bin/zsm-gui" /usr/local/bin/zsm-gui
mkdir -p /etc/zsm /var/lib/zsm/backups /var/lib/zsm/reports /var/log/zsm
if [[ ! -f /etc/zsm/config.json ]]; then cp "$PREFIX/source/config.example.json" /etc/zsm/config.json; fi
cat > /usr/share/applications/zsm.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Zima Storage Manager
Comment=ZimaOS storage administration
Exec=/usr/local/bin/zsm-gui
Terminal=false
Categories=System;Settings;
EOF
echo "Installed. Launch with: zsm-gui or zsm status"

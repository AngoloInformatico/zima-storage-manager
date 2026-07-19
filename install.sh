#!/usr/bin/env bash
set -euo pipefail

REPO="AngoloInformatico/zima-storage-manager"
PREFIX="/opt/zima-storage-manager"
SOURCE="$PREFIX/source"
VENV="$PREFIX/.venv"
SERVICE="/etc/systemd/system/zima-storage-manager.service"
ENV_FILE="/etc/zsm/zsm.env"

if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  echo "Esegui con sudo: sudo bash install.sh" >&2
  exit 1
fi

echo "=== Zima Storage Manager ==="
echo "Installazione guidata per ZimaOS"

command -v python3 >/dev/null || {
  echo "Python 3 non trovato. Installazione..."
  apt-get update
  apt-get install -y python3 python3-venv python3-pip
}

mkdir -p "$PREFIX" /etc/zsm /var/lib/zsm/backups /var/lib/zsm/reports /var/log/zsm

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rm -rf "$SOURCE"
mkdir -p "$SOURCE"
cp -a "$SCRIPT_DIR"/. "$SOURCE"/

python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install "$SOURCE"

ln -sf "$VENV/bin/zsm" /usr/local/bin/zsm
ln -sf "$VENV/bin/zsm-web" /usr/local/bin/zsm-web

if [[ ! -f /etc/zsm/config.json ]]; then
  cp "$SOURCE/config.example.json" /etc/zsm/config.json
fi

if [[ ! -f "$ENV_FILE" ]]; then
  TOKEN="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(9))
PY
)"
  cat > "$ENV_FILE" <<EOF
ZSM_HOST=0.0.0.0
ZSM_PORT=8765
ZSM_TOKEN=$TOKEN
EOF
  chmod 600 "$ENV_FILE"
fi

cat > "$SERVICE" <<EOF
[Unit]
Description=Zima Storage Manager Web
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=$ENV_FILE
ExecStart=$VENV/bin/zsm-web
Restart=on-failure
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now zima-storage-manager.service

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
TOKEN="$(sed -n 's/^ZSM_TOKEN=//p' "$ENV_FILE")"

echo
echo "Installazione completata."
echo "Apri dal browser:"
echo "  http://${IP:-IP_DEL_TUO_ZIMAOS}:8765"
echo
echo "Codice di accesso:"
echo "  $TOKEN"
echo
echo "Conserva questo codice. Per rivederlo:"
echo "  sudo cat $ENV_FILE"

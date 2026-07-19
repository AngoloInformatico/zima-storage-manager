#!/usr/bin/env bash
set -euo pipefail

REPO="AngoloInformatico/zima-storage-manager"
BRANCH="${ZSM_BRANCH:-main}"
PREFIX="/opt/zima-storage-manager"
SOURCE="$PREFIX/source"
VENV="$PREFIX/.venv"
ENV_DIR="/etc/zsm"
ENV_FILE="$ENV_DIR/zsm.env"
SERVICE="/etc/systemd/system/zima-storage-manager.service"
PORT="${ZSM_PORT:-8765}"
TMP=""

cleanup() {
  [[ -n "${TMP:-}" && -d "$TMP" ]] && rm -rf "$TMP"
}
trap cleanup EXIT

fail() {
  echo
  echo "ERRORE: $*" >&2
  exit 1
}

[[ ${EUID:-$(id -u)} -eq 0 ]] || fail "esegui l'installazione con sudo."

echo "================================================"
echo " Zima Storage Manager - Installazione guidata"
echo "================================================"

command -v python3 >/dev/null 2>&1 || fail "Python 3 non è presente su questo sistema."
python3 -m venv --help >/dev/null 2>&1 || fail "Il modulo python3-venv non è disponibile."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-.}")" 2>/dev/null && pwd || true)"
if [[ -f "$SCRIPT_DIR/pyproject.toml" && -d "$SCRIPT_DIR/zsm" ]]; then
  LOCAL_SOURCE="$SCRIPT_DIR"
else
  echo "[1/5] Download dell'ultima versione..."
  TMP="$(mktemp -d)"
  ARCHIVE="$TMP/zsm.tar.gz"
  URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.tar.gz"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$URL" -o "$ARCHIVE"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$ARCHIVE" "$URL"
  else
    fail "serve curl oppure wget per scaricare ZSM."
  fi
  tar -xzf "$ARCHIVE" -C "$TMP"
  LOCAL_SOURCE="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n1)"
fi

echo "[2/5] Copia dei file..."
mkdir -p "$PREFIX" "$ENV_DIR" /var/lib/zsm/backups /var/lib/zsm/reports /var/log/zsm
rm -rf "$SOURCE"
mkdir -p "$SOURCE"
cp -a "$LOCAL_SOURCE"/. "$SOURCE"/

echo "[3/5] Preparazione dell'applicazione..."
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --disable-pip-version-check --no-cache-dir "$SOURCE"

if [[ ! -f "$ENV_DIR/config.json" ]]; then
  cp "$SOURCE/config.example.json" "$ENV_DIR/config.json"
fi

if [[ ! -f "$ENV_FILE" ]]; then
  PASSWORD="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(9))
PY
)"
  cat > "$ENV_FILE" <<EOF
ZSM_HOST=0.0.0.0
ZSM_PORT=$PORT
ZSM_PASSWORD=$PASSWORD
ZSM_COOKIE_SECURE=0
EOF
  chmod 600 "$ENV_FILE"
fi

echo "[4/5] Creazione del servizio automatico..."
cat > "$SERVICE" <<EOF
[Unit]
Description=Zima Storage Manager
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
EnvironmentFile=$ENV_FILE
ExecStart=$VENV/bin/zsm-web
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=full
ReadWritePaths=/var/lib/casaos /var/lib/zsm /var/log/zsm /etc/zsm
LockPersonality=true

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/bin/zsm-update <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
URL="https://github.com/AngoloInformatico/zima-storage-manager/archive/refs/heads/main.tar.gz"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "$URL" -o "$TMP/zsm.tar.gz"
else
  wget -qO "$TMP/zsm.tar.gz" "$URL"
fi
tar -xzf "$TMP/zsm.tar.gz" -C "$TMP"
DIR="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -n1)"
bash "$DIR/install.sh"
EOF
chmod +x /usr/local/bin/zsm-update

ln -sf "$VENV/bin/zsm" /usr/local/bin/zsm
ln -sf "$VENV/bin/zsm-web" /usr/local/bin/zsm-web

systemctl daemon-reload
systemctl enable --now zima-storage-manager.service

echo "[5/5] Verifica..."
sleep 2
systemctl is-active --quiet zima-storage-manager.service || {
  systemctl status zima-storage-manager.service --no-pager || true
  fail "il servizio non si è avviato."
}

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
PASSWORD="$(sed -n 's/^ZSM_PASSWORD=//p' "$ENV_FILE")"

echo
echo "================================================"
echo " INSTALLAZIONE COMPLETATA"
echo "================================================"
echo
echo "Apri questo indirizzo dal PC o dallo smartphone:"
echo "  http://${IP:-IP_DEL_TUO_ZIMAOS}:$PORT"
echo
echo "Codice di accesso:"
echo "  $PASSWORD"
echo
echo "Conserva il codice in un luogo sicuro."
echo "Per aggiornare in futuro: sudo zsm-update"

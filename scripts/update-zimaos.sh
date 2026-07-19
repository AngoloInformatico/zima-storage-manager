#!/usr/bin/env bash
set -Eeuo pipefail

REPO="AngoloInformatico/zima-storage-manager"
VERSION="${ZSM_VERSION:-3.0.0-rc7}"
TAG="v${VERSION}"
APP_ID="zima-storage-manager"
APP_DIR="/var/lib/casaos/apps/${APP_ID}"
COMPOSE_FILE="${APP_DIR}/docker-compose.yml"
DATA_DIR="/DATA/AppData/${APP_ID}"
BACKUP_ROOT="${DATA_DIR}/updater-backups"
STAMP="$(date +%Y%m%d-%H%M%S)"
ROLLBACK_DIR="${BACKUP_ROOT}/${STAMP}"
TMP="$(mktemp -d)"
OLD_CONTAINER=""
OLD_IMAGE=""

cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

log() { printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"; }
fail() { printf '\nERRORE: %s\n' "$*" >&2; exit 1; }
fetch() {
  local url="$1" out="$2"
  if command -v curl >/dev/null 2>&1; then curl -fsSL "$url" -o "$out"
  elif command -v wget >/dev/null 2>&1; then wget -qO "$out" "$url"
  else fail "serve curl oppure wget"; fi
}
compose() {
  if docker compose version >/dev/null 2>&1; then docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then docker-compose "$@"
  else fail "Docker Compose non è disponibile"; fi
}
rollback() {
  local rc=$?
  trap - ERR
  printf '\nAggiornamento fallito. Avvio rollback...\n' >&2
  if [[ -f "${ROLLBACK_DIR}/docker-compose.yml" ]]; then
    cp -f "${ROLLBACK_DIR}/docker-compose.yml" "$COMPOSE_FILE"
    cd "$APP_DIR"
    compose up -d --force-recreate || true
  fi
  exit "$rc"
}
trap rollback ERR

[[ ${EUID:-$(id -u)} -eq 0 ]] || fail "esegui con sudo"
command -v docker >/dev/null 2>&1 || fail "Docker non è installato"

log "Preparazione cartelle persistenti"
mkdir -p "$APP_DIR" "$DATA_DIR/backups" "$DATA_DIR/reports" "$DATA_DIR/logs" "$ROLLBACK_DIR"

OLD_CONTAINER="$(docker ps -a --filter name=${APP_ID} --format '{{.Names}}' | head -n1 || true)"
if [[ -n "$OLD_CONTAINER" ]]; then
  OLD_IMAGE="$(docker inspect "$OLD_CONTAINER" --format '{{.Config.Image}}' 2>/dev/null || true)"
  printf 'Container trovato: %s\nImmagine attuale: %s\n' "$OLD_CONTAINER" "${OLD_IMAGE:-sconosciuta}"

  log "Salvataggio dei dati eventualmente ancora interni al vecchio container"
  docker cp "$OLD_CONTAINER:/var/lib/zsm/backups/." "$DATA_DIR/backups/" 2>/dev/null || true
  docker cp "$OLD_CONTAINER:/var/lib/zsm/reports/." "$DATA_DIR/reports/" 2>/dev/null || true
  docker cp "$OLD_CONTAINER:/var/log/zsm/." "$DATA_DIR/logs/" 2>/dev/null || true
fi

if [[ -f "$COMPOSE_FILE" ]]; then
  cp -a "$COMPOSE_FILE" "$ROLLBACK_DIR/docker-compose.yml"
fi

log "Download del Compose ufficiale ${TAG}"
URL="https://raw.githubusercontent.com/${REPO}/${TAG}/docker-compose.yml"
fetch "$URL" "$TMP/docker-compose.yml"
grep -q "zima-storage-manager:v${VERSION}" "$TMP/docker-compose.yml" || fail "il Compose scaricato non corrisponde a ${TAG}"
cp -f "$TMP/docker-compose.yml" "$COMPOSE_FILE"

# Mantiene la password esistente, quando presente, tramite file .env gestito dall'updater.
PASSWORD=""
if [[ -f "$APP_DIR/.env" ]]; then
  PASSWORD="$(sed -n 's/^ZSM_PASSWORD=//p' "$APP_DIR/.env" | tail -n1)"
fi
if [[ -z "$PASSWORD" && -n "$OLD_CONTAINER" ]]; then
  PASSWORD="$(docker inspect "$OLD_CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | sed -n 's/^ZSM_PASSWORD=//p' | tail -n1 || true)"
fi
if [[ -z "$PASSWORD" || "$PASSWORD" == "zima-storage-manager" ]]; then
  PASSWORD="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(12))
PY
)"
fi
cat > "$APP_DIR/.env" <<EOF
ZSM_PASSWORD=$PASSWORD
TZ=${TZ:-Europe/Rome}
EOF
chmod 600 "$APP_DIR/.env"

log "Validazione del Compose"
cd "$APP_DIR"
compose config >/dev/null

log "Download immagine ${TAG}"
compose pull

log "Ricreazione controllata del container"
compose up -d --force-recreate --remove-orphans

log "Attesa healthcheck"
CONTAINER="$(docker ps --filter name=${APP_ID} --format '{{.Names}}' | head -n1)"
[[ -n "$CONTAINER" ]] || fail "container non trovato dopo l'avvio"
for _ in $(seq 1 30); do
  STATUS="$(docker inspect "$CONTAINER" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
  [[ "$STATUS" == "healthy" ]] && break
  [[ "$STATUS" == "unhealthy" || "$STATUS" == "exited" ]] && fail "container in stato ${STATUS}"
  sleep 2
done
STATUS="$(docker inspect "$CONTAINER" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
[[ "$STATUS" == "healthy" ]] || fail "healthcheck non completato: ${STATUS}"

log "Verifica versione applicativa"
RUNNING_VERSION="$(docker exec "$CONTAINER" python -c 'import zsm; print(zsm.__version__)')"
[[ "$RUNNING_VERSION" == "$VERSION" ]] || fail "versione attiva ${RUNNING_VERSION}, attesa ${VERSION}"

log "Verifica volumi persistenti"
MOUNTS="$(docker inspect "$CONTAINER" --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}')"
for target in /var/lib/zsm/backups /var/lib/zsm/reports /var/log/zsm; do
  grep -q -- "-> $target" <<<"$MOUNTS" || fail "mount persistente mancante: $target"
done

trap - ERR
printf '\n================================================\n'
printf ' AGGIORNAMENTO COMPLETATO: v%s\n' "$VERSION"
printf '================================================\n'
printf 'Interfaccia: http://IP_DEL_SERVER:8787\n'
printf 'Password: %s\n' "$PASSWORD"
printf 'Backup configurazione precedente: %s\n' "$ROLLBACK_DIR"

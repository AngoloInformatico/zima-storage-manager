#!/usr/bin/env bash
set -Eeuo pipefail
VERSION="${ZSM_VERSION:-3.0.0-rc9}"
export ZSM_VERSION="$VERSION"
URL="https://raw.githubusercontent.com/AngoloInformatico/zima-storage-manager/v${VERSION}/scripts/update-zimaos.sh"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
if command -v curl >/dev/null 2>&1; then curl -fsSL "$URL" -o "$TMP"
elif command -v wget >/dev/null 2>&1; then wget -qO "$TMP" "$URL"
else echo "ERRORE: serve curl oppure wget" >&2; exit 1; fi
exec bash "$TMP"

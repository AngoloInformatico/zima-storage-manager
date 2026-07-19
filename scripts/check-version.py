#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
errors: list[str] = []

def expect(path: str, pattern: str, expected: str) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(pattern, text, re.MULTILINE)
    actual = match.group(1) if match else None
    if actual != expected:
        errors.append(f"{path}: atteso {expected!r}, trovato {actual!r}")

expect("pyproject.toml", r'^version\s*=\s*"([^"]+)"', version)
expect("zsm/__init__.py", r'^__version__\s*=\s*"([^"]+)"', version)
expect("docker-compose.yml", r'image:\s*ghcr\.io/angoloinformatico/zima-storage-manager:v([^\s]+)', version)

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if f"v{version}" not in readme:
    errors.append(f"README.md: manca v{version}")
if "img/zima-storage-manager-dashboard.png" not in readme and "./img/zima-storage-manager-dashboard.png" not in readme:
    errors.append("README.md: manca l'immagine dashboard")
if not (ROOT / "img/zima-storage-manager-dashboard.png").is_file():
    errors.append("img/zima-storage-manager-dashboard.png: file mancante")

if errors:
    print("Controllo versione FALLITO:", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)
print(f"Controllo versione OK: {version}")

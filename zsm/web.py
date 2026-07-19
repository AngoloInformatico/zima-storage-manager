from __future__ import annotations

import html
import json
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from .config import Config
from .core.manager import StorageManager


def _page(title: str, body: str) -> bytes:
    document = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Zima Storage Manager</title>
<style>
:root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
body {{ margin:0; background:#0b1220; color:#e5e7eb; }}
main {{ max-width:760px; margin:auto; padding:28px 18px 60px; }}
.card {{ background:#111827; border:1px solid #263244; border-radius:16px; padding:22px; margin:18px 0; }}
h1 {{ font-size:1.8rem; margin:.2rem 0; }}
h2 {{ font-size:1.15rem; }}
p {{ color:#b7c1d1; line-height:1.55; }}
label {{ display:block; margin:14px 0 6px; font-weight:700; }}
select,input,button {{ width:100%; box-sizing:border-box; padding:14px; border-radius:10px; border:1px solid #3b4658; font-size:1rem; }}
select,input {{ background:#0f172a; color:#fff; }}
button {{ margin-top:18px; border:0; background:#2563eb; color:white; font-weight:800; cursor:pointer; }}
button:hover {{ background:#1d4ed8; }}
.warning {{ background:#3a2604; border-color:#8a5a00; }}
.ok {{ background:#0d3324; border-color:#167a50; }}
.small {{ font-size:.9rem; }}
code {{ color:#bfdbfe; }}
</style>
</head>
<body><main>{body}</main></body></html>"""
    return document.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    manager = StorageManager(Config.load())
    token = os.environ.get("ZSM_TOKEN", "")

    def _authorized(self) -> bool:
        if not self.token:
            return True
        return self.headers.get("X-ZSM-Token", "") == self.token

    def _send(self, content: bytes, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            disks = self.manager.disks()
            options = []
            for disk in disks:
                label = disk.label or "Senza etichetta"
                device = disk.device or "non collegato"
                current = disk.mount_point or "-"
                text = f"{label} — {device} — {current}"
                options.append(
                    f'<option value="{html.escape(disk.uuid)}">{html.escape(text)}</option>'
                )
            disk_select = "\n".join(options) or '<option value="">Nessun disco trovato</option>'
            token_field = (
                '<label>Codice di accesso</label><input name="token" type="password" required>'
                if self.token else ""
            )
            body = f"""
<h1>Zima Storage Manager</h1>
<p>Rinomina il punto di montaggio di un disco ZimaOS senza usare comandi o UUID.</p>
<div class="card warning">
<strong>Prima di continuare</strong>
<p class="small">Ferma eventuali trasferimenti e applicazioni che stanno usando il disco. ZSM crea automaticamente un backup del database prima della modifica.</p>
</div>
<form class="card" method="post" action="/rename">
<h2>1. Scegli il disco</h2>
<select name="uuid" required>{disk_select}</select>
<h2>2. Scrivi il nuovo nome</h2>
<label>Nuova etichetta</label>
<input name="name" placeholder="Esempio: NAS3" pattern="[A-Za-z0-9._-]{{1,64}}" maxlength="64" required>
{token_field}
<button type="submit">Rinomina disco</button>
</form>
<p class="small">La modifica riguarda il nome usato da ZimaOS per montare il disco. Non formatta il disco e non cancella i dati.</p>
"""
            self._send(_page("Rinomina disco", body))
        except Exception as exc:
            self._send(_page("Errore", f'<div class="card warning"><h1>Errore</h1><p>{html.escape(str(exc))}</p></div>'), HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        if self.path != "/rename":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        uuid = form.get("uuid", [""])[0].strip()
        name = form.get("name", [""])[0].strip()
        supplied_token = form.get("token", [""])[0]
        if self.token and not secrets.compare_digest(supplied_token, self.token):
            self._send(_page("Accesso negato", '<div class="card warning"><h1>Codice non valido</h1><p>Torna indietro e riprova.</p></div>'), HTTPStatus.FORBIDDEN)
            return
        try:
            result = self.manager.rename(uuid, name)
            backup = html.escape(result.get("backup", ""))
            body = f"""
<div class="card ok">
<h1>Rinomina completata</h1>
<p>Nuovo percorso: <code>{html.escape(result["new"])}</code></p>
<p class="small">Backup automatico: <code>{backup}</code></p>
</div>
<a href="/">Torna alla schermata principale</a>
"""
            self._send(_page("Operazione completata", body))
        except Exception as exc:
            self._send(_page("Errore", f'<div class="card warning"><h1>Operazione non riuscita</h1><p>{html.escape(str(exc))}</p></div><a href="/">Torna indietro</a>'), HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    host = os.environ.get("ZSM_HOST", "0.0.0.0")
    port = int(os.environ.get("ZSM_PORT", "8765"))
    print(f"Zima Storage Manager disponibile su http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()

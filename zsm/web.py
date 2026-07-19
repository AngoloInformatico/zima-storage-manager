from __future__ import annotations

import hashlib
import html
import os
import secrets
import time
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote

from .config import Config
from .core.manager import StorageManager

APP_VERSION = "2.0.0"
SESSION_TTL = 12 * 60 * 60
SESSIONS: dict[str, float] = {}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{esc(title)} · Zima Storage Manager</title>
<style>
:root {{
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --bg:#09111f; --panel:#111b2d; --panel2:#162238; --line:#2a3850;
  --text:#f4f7fb; --muted:#aab6c8; --blue:#3b82f6; --blue2:#2563eb;
  --green:#22c55e; --amber:#f59e0b; --red:#ef4444;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; min-height:100vh; background:radial-gradient(circle at top,#152747 0,#09111f 44%); color:var(--text); }}
main {{ width:min(920px,100%); margin:auto; padding:28px 18px 64px; }}
header {{ display:flex; justify-content:space-between; align-items:center; gap:16px; margin-bottom:26px; }}
.brand {{ display:flex; align-items:center; gap:14px; }}
.logo {{ width:48px; height:48px; border-radius:14px; display:grid; place-items:center; background:linear-gradient(145deg,#60a5fa,#2563eb); font-size:25px; box-shadow:0 12px 30px #0006; }}
h1 {{ margin:0; font-size:clamp(1.55rem,4vw,2.15rem); }}
h2 {{ margin:0 0 8px; font-size:1.15rem; }}
p {{ color:var(--muted); line-height:1.55; }}
.version {{ color:var(--muted); font-size:.8rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(270px,1fr)); gap:16px; }}
.card {{ background:linear-gradient(145deg,var(--panel2),var(--panel)); border:1px solid var(--line); border-radius:18px; padding:20px; box-shadow:0 16px 35px #0004; }}
.disk-top {{ display:flex; gap:14px; align-items:center; }}
.disk-icon {{ width:48px; height:48px; border-radius:13px; display:grid; place-items:center; background:#0c1628; border:1px solid var(--line); font-size:24px; }}
.disk-name {{ font-size:1.18rem; font-weight:800; word-break:break-word; }}
.meta {{ margin:14px 0 18px; display:flex; flex-wrap:wrap; gap:8px; }}
.badge {{ background:#0c1628; border:1px solid var(--line); color:#c9d5e6; border-radius:999px; padding:6px 10px; font-size:.82rem; }}
button,.button {{ display:inline-flex; justify-content:center; align-items:center; width:100%; border:0; border-radius:12px; padding:13px 16px; background:var(--blue); color:white; font:inherit; font-weight:800; cursor:pointer; text-decoration:none; }}
button:hover,.button:hover {{ background:var(--blue2); }}
.secondary {{ background:#25334a; }}
.secondary:hover {{ background:#31415c; }}
.danger {{ background:#b91c1c; }}
input {{ width:100%; margin-top:7px; padding:14px; border-radius:11px; border:1px solid #42516a; background:#0b1527; color:white; font:inherit; outline:none; }}
input:focus {{ border-color:#60a5fa; box-shadow:0 0 0 3px #3b82f633; }}
label {{ display:block; margin:16px 0 5px; font-weight:750; }}
.notice {{ border-left:4px solid var(--amber); }}
.success {{ border-left:4px solid var(--green); }}
.error {{ border-left:4px solid var(--red); }}
.actions {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:18px; }}
.empty {{ text-align:center; padding:36px 22px; }}
.small {{ font-size:.9rem; }}
footer {{ margin-top:25px; text-align:center; color:var(--muted); font-size:.83rem; }}
code {{ color:#bfdbfe; word-break:break-all; }}
@media (max-width:520px) {{
  header {{ align-items:flex-start; }}
  .actions {{ grid-template-columns:1fr; }}
}}
</style>
</head>
<body><main>{body}<footer>Zima Storage Manager v{APP_VERSION} · Created by Alex Lignola</footer></main></body>
</html>""".encode("utf-8")


class AppHandler(BaseHTTPRequestHandler):
    config = Config.load()
    manager = StorageManager(config)
    password = os.environ.get("ZSM_PASSWORD", "")
    cookie_secure = os.environ.get("ZSM_COOKIE_SECURE", "0") == "1"

    def _send(self, content: bytes, status: HTTPStatus = HTTPStatus.OK, headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def _redirect(self, path: str, headers: dict[str, str] | None = None) -> None:
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", path)
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()

    def _form(self) -> dict[str, str]:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 32_768:
            raise ValueError("Richiesta troppo grande")
        values = parse_qs(self.rfile.read(size).decode("utf-8"), keep_blank_values=True)
        return {key: items[0] for key, items in values.items()}

    def _session_id(self) -> str:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get("zsm_session")
        return morsel.value if morsel else ""

    def _authenticated(self) -> bool:
        if not self.password:
            return True
        now = time.time()
        expired = [sid for sid, deadline in SESSIONS.items() if deadline < now]
        for sid in expired:
            SESSIONS.pop(sid, None)
        sid = self._session_id()
        return bool(sid and SESSIONS.get(sid, 0) >= now)

    def _require_login(self) -> bool:
        if self._authenticated():
            return True
        self._redirect("/login")
        return False

    def _header(self) -> str:
        return """
<header>
  <div class="brand"><div class="logo">💾</div><div><h1>Zima Storage Manager</h1><div class="version">Rinomina dischi in modo semplice e sicuro</div></div></div>
</header>
"""

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/health":
            self._send(b"OK")
            return
        if path == "/login":
            self._login_page()
            return
        if path == "/logout":
            sid = self._session_id()
            SESSIONS.pop(sid, None)
            cookie = "zsm_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"
            self._redirect("/login", {"Set-Cookie": cookie})
            return
        if not self._require_login():
            return
        if path == "/":
            self._home()
        elif path == "/rename":
            self._rename_page()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/login":
            self._login()
            return
        if not self._require_login():
            return
        if path == "/confirm":
            self._confirm()
        elif path == "/apply":
            self._apply()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def _login_page(self, error: str = "") -> None:
        if self._authenticated():
            self._redirect("/")
            return
        error_box = f'<div class="card error"><strong>{esc(error)}</strong></div>' if error else ""
        body = self._header() + f"""
{error_box}
<form class="card" method="post" action="/login">
  <h2>Accesso</h2>
  <p>Inserisci il codice mostrato al termine dell'installazione.</p>
  <label for="password">Codice di accesso</label>
  <input id="password" name="password" type="password" autocomplete="current-password" autofocus required>
  <button type="submit">Entra</button>
</form>
"""
        self._send(page("Accesso", body), HTTPStatus.UNAUTHORIZED if error else HTTPStatus.OK)

    def _login(self) -> None:
        supplied = self._form().get("password", "")
        if not self.password or secrets.compare_digest(supplied, self.password):
            sid = secrets.token_urlsafe(32)
            SESSIONS[sid] = time.time() + SESSION_TTL
            cookie = f"zsm_session={sid}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}"
            if self.cookie_secure:
                cookie += "; Secure"
            self._redirect("/", {"Set-Cookie": cookie})
            return
        time.sleep(0.6)
        self._login_page("Codice non corretto.")

    def _home(self) -> None:
        try:
            disks = self.manager.disks()
        except Exception as exc:
            body = self._header() + f'<div class="card error"><h2>Impossibile leggere i dischi</h2><p>{esc(exc)}</p></div>'
            self._send(page("Errore", body), HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        cards: list[str] = []
        for disk in disks:
            shown_name = disk.label or self._mount_name(disk.mount_point) or "Disco senza nome"
            mount_name = self._mount_name(disk.mount_point)
            connected = bool(disk.device)
            badges = [
                f'<span class="badge">{esc(disk.size or "Dimensione sconosciuta")}</span>',
                f'<span class="badge">{esc((disk.fs_type or "filesystem sconosciuto").upper())}</span>',
                f'<span class="badge">{"Collegato" if connected else "Non collegato"}</span>',
            ]
            if mount_name and mount_name != shown_name:
                badges.append(f'<span class="badge">ZimaOS: {esc(mount_name)}</span>')
            disabled_note = "" if connected else "<p class='small'>Il disco non risulta collegato, ma il nome registrato può comunque essere modificato.</p>"
            cards.append(f"""
<article class="card">
  <div class="disk-top">
    <div class="disk-icon">🗄️</div>
    <div><div class="disk-name">{esc(shown_name)}</div><div class="small">{esc(disk.device or "Dispositivo non rilevato")}</div></div>
  </div>
  <div class="meta">{''.join(badges)}</div>
  {disabled_note}
  <a class="button" href="/rename?id={quote(disk.uuid)}">Cambia nome</a>
</article>
""")
        if not cards:
            content = """
<div class="card empty">
  <div style="font-size:42px">🔌</div>
  <h2>Nessun disco disponibile</h2>
  <p>Collega un disco a ZimaOS e aggiorna la pagina.</p>
</div>
"""
        else:
            content = '<div class="grid">' + "".join(cards) + "</div>"

        body = self._header() + """
<div class="card notice">
  <strong>Cosa viene rinominato?</strong>
  <p class="small">ZSM cambia il nome del percorso usato da ZimaOS per montare il disco. Non modifica l'etichetta interna del filesystem, non formatta il disco e non cancella file.</p>
</div>
""" + content + '<p class="small" style="text-align:right"><a href="/logout" style="color:#aab6c8">Esci</a></p>'
        self._send(page("I tuoi dischi", body))

    @staticmethod
    def _mount_name(path: str) -> str:
        return path.rstrip("/").rsplit("/", 1)[-1] if path else ""

    def _disk(self, uuid: str):
        return next((disk for disk in self.manager.disks() if disk.uuid == uuid), None)

    def _query_value(self, key: str) -> str:
        query = self.path.split("?", 1)[1] if "?" in self.path else ""
        return parse_qs(query).get(key, [""])[0]

    def _rename_page(self) -> None:
        uuid = self._query_value("id")
        disk = self._disk(uuid)
        if not disk:
            self._send(page("Disco non trovato", self._header() + '<div class="card error"><h2>Disco non trovato</h2><a class="button secondary" href="/">Torna indietro</a></div>'), HTTPStatus.NOT_FOUND)
            return
        current = self._mount_name(disk.mount_point)
        body = self._header() + f"""
<form class="card" method="post" action="/confirm">
  <h2>Nuovo nome del disco</h2>
  <p>Stai rinominando <strong>{esc(disk.label or current or disk.device)}</strong>.</p>
  <input type="hidden" name="uuid" value="{esc(disk.uuid)}">
  <label for="name">Nuovo nome</label>
  <input id="name" name="name" value="{esc(current)}" maxlength="64" autocomplete="off" autofocus required>
  <p class="small">Usa lettere, numeri, spazi, punto, trattino o trattino basso.</p>
  <div class="actions"><a class="button secondary" href="/">Annulla</a><button type="submit">Continua</button></div>
</form>
"""
        self._send(page("Cambia nome", body))

    def _confirm(self) -> None:
        form = self._form()
        uuid, name = form.get("uuid", ""), form.get("name", "").strip()
        disk = self._disk(uuid)
        if not disk:
            self._send(page("Errore", self._header() + '<div class="card error"><h2>Disco non trovato</h2></div>'), HTTPStatus.BAD_REQUEST)
            return
        current = self._mount_name(disk.mount_point)
        nonce = secrets.token_urlsafe(20)
        digest = hashlib.sha256(f"{self._session_id()}:{uuid}:{name}:{nonce}".encode()).hexdigest()
        SESSIONS[f"confirm:{digest}"] = time.time() + 300
        body = self._header() + f"""
<form class="card notice" method="post" action="/apply">
  <h2>Conferma la modifica</h2>
  <p>Il nome usato da ZimaOS cambierà da:</p>
  <p><code>{esc(current or disk.mount_point)}</code></p>
  <p>a:</p>
  <p><code>{esc(name)}</code></p>
  <input type="hidden" name="uuid" value="{esc(uuid)}">
  <input type="hidden" name="name" value="{esc(name)}">
  <input type="hidden" name="nonce" value="{esc(nonce)}">
  <input type="hidden" name="proof" value="{esc(digest)}">
  <p class="small">Prima della modifica verrà creato automaticamente un backup. Durante l'operazione il servizio di archiviazione potrebbe fermarsi per pochi secondi.</p>
  <div class="actions"><a class="button secondary" href="/">Annulla</a><button class="danger" type="submit">Conferma e rinomina</button></div>
</form>
"""
        self._send(page("Conferma", body))

    def _apply(self) -> None:
        form = self._form()
        uuid = form.get("uuid", "")
        name = form.get("name", "").strip()
        nonce = form.get("nonce", "")
        proof = form.get("proof", "")
        expected = hashlib.sha256(f"{self._session_id()}:{uuid}:{name}:{nonce}".encode()).hexdigest()
        key = f"confirm:{proof}"
        deadline = SESSIONS.pop(key, 0)
        if not secrets.compare_digest(proof, expected) or deadline < time.time():
            self._send(page("Conferma scaduta", self._header() + '<div class="card error"><h2>Conferma non valida o scaduta</h2><a class="button secondary" href="/">Torna alla schermata principale</a></div>'), HTTPStatus.BAD_REQUEST)
            return
        try:
            result = self.manager.rename(uuid, name)
            body = self._header() + f"""
<div class="card success">
  <h2>Nome modificato correttamente</h2>
  <p>Il nuovo percorso registrato è:</p>
  <p><code>{esc(result["new"])}</code></p>
  <p class="small">Backup creato: <code>{esc(result.get("backup", "automatico"))}</code></p>
  <a class="button" href="/">Fine</a>
</div>
<div class="card notice"><p class="small">Se il nuovo nome non appare immediatamente nell'interfaccia di ZimaOS, attendi qualche secondo e aggiorna la pagina di ZimaOS. In alcuni casi può essere necessario riavviare il sistema.</p></div>
"""
            self._send(page("Operazione completata", body))
        except Exception as exc:
            body = self._header() + f"""
<div class="card error">
  <h2>Modifica non riuscita</h2>
  <p>{esc(exc)}</p>
  <p class="small">ZSM ha tentato il ripristino automatico del database.</p>
  <a class="button secondary" href="/">Torna indietro</a>
</div>
"""
            self._send(page("Errore", body), HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    host = os.environ.get("ZSM_HOST", "0.0.0.0")
    port = int(os.environ.get("ZSM_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Zima Storage Manager v{APP_VERSION} attivo su http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

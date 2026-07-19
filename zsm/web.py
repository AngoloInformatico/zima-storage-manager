from __future__ import annotations

import hashlib
import html
import os
import secrets
import time
import threading
from datetime import datetime
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

from . import __version__
from .config import Config
from .core.manager import StorageManager
from .core.system import validate_name

APP_VERSION = __version__
SESSION_TTL = 12 * 60 * 60
CONFIRM_TTL = 10 * 60
SESSIONS: dict[str, dict[str, object]] = {}
SESSIONS_LOCK = threading.RLock()
NOAUTH_SESSION: dict[str, object] = {"expires": float("inf"), "csrf": "no-auth"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def page(title: str, body: str) -> bytes:
    return f"""<!doctype html><html lang="it"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{esc(title)} · Zima Storage Manager</title>
<style>
:root{{color-scheme:dark;font-family:Inter,system-ui,sans-serif;--bg:#09111f;--panel:#111b2d;--panel2:#162238;--line:#2a3850;--text:#f4f7fb;--muted:#aab6c8;--blue:#3b82f6;--blue2:#2563eb;--green:#22c55e;--amber:#f59e0b;--red:#ef4444}}
*{{box-sizing:border-box}}body{{margin:0;min-height:100vh;background:radial-gradient(circle at top,#152747 0,#09111f 44%);color:var(--text)}}main{{width:min(1020px,100%);margin:auto;padding:24px 18px 64px}}header{{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:18px}}.brand{{display:flex;align-items:center;gap:14px}}.logo{{width:48px;height:48px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,#60a5fa,#2563eb);font-size:25px}}h1{{margin:0;font-size:clamp(1.45rem,4vw,2.05rem)}}h2{{margin:0 0 8px;font-size:1.15rem}}p{{color:var(--muted);line-height:1.55}}.version,.small{{color:var(--muted);font-size:.86rem}}nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 22px}}nav a{{padding:9px 12px;border-radius:10px;background:#152238;border:1px solid var(--line);color:#dce8f8;text-decoration:none;font-size:.9rem}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px}}.card{{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:18px;padding:20px;margin-bottom:16px;box-shadow:0 16px 35px #0004}}.disk-top{{display:flex;gap:14px;align-items:center}}.disk-icon{{width:48px;height:48px;border-radius:13px;display:grid;place-items:center;background:#0c1628;border:1px solid var(--line);font-size:24px}}.disk-name{{font-size:1.18rem;font-weight:800;word-break:break-word}}.meta{{margin:14px 0 18px;display:flex;flex-wrap:wrap;gap:8px}}.badge{{background:#0c1628;border:1px solid var(--line);color:#c9d5e6;border-radius:999px;padding:6px 10px;font-size:.82rem}}button,.button{{display:inline-flex;justify-content:center;align-items:center;width:100%;border:0;border-radius:12px;padding:13px 16px;background:var(--blue);color:white;font:inherit;font-weight:800;cursor:pointer;text-decoration:none}}button:hover,.button:hover{{background:var(--blue2)}}.secondary{{background:#25334a}}.danger{{background:#b91c1c}}input{{width:100%;margin-top:7px;padding:14px;border-radius:11px;border:1px solid #42516a;background:#0b1527;color:white;font:inherit}}label{{display:block;margin:16px 0 5px;font-weight:750}}.notice{{border-left:4px solid var(--amber)}}.success{{border-left:4px solid var(--green)}}.error{{border-left:4px solid var(--red)}}.actions{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}}.row{{display:flex;justify-content:space-between;gap:16px;align-items:center;padding:13px 0;border-bottom:1px solid var(--line)}}.row:last-child{{border-bottom:0}}.row form{{min-width:150px}}code{{color:#bfdbfe;word-break:break-all}}footer{{margin-top:25px;text-align:center;color:var(--muted);font-size:.83rem}}@media(max-width:600px){{header,.row{{align-items:flex-start;flex-direction:column}}.actions{{grid-template-columns:1fr}}.row form{{width:100%}}}}
</style></head><body><main>{body}<footer>Zima Storage Manager v{APP_VERSION} · Created by Alex Lignola</footer></main></body></html>""".encode()


class AppHandler(BaseHTTPRequestHandler):
    config = Config.load()
    manager = StorageManager(config)
    password = os.environ.get("ZSM_PASSWORD", "")
    cookie_secure = os.environ.get("ZSM_COOKIE_SECURE", "0") == "1"

    def _send(self, content: bytes, status: HTTPStatus = HTTPStatus.OK, content_type: str = "text/html; charset=utf-8", headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        for key, value in (headers or {}).items(): self.send_header(key, value)
        self.end_headers(); self.wfile.write(content)

    def _redirect(self, path: str, headers: dict[str, str] | None = None) -> None:
        self.send_response(HTTPStatus.SEE_OTHER); self.send_header("Location", path); self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items(): self.send_header(key, value)
        self.end_headers()

    def _form(self) -> dict[str, str]:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 32768: raise ValueError("Richiesta troppo grande")
        values = parse_qs(self.rfile.read(size).decode(), keep_blank_values=True)
        return {key: items[0] for key, items in values.items()}

    def _session_id(self) -> str:
        cookie = SimpleCookie(self.headers.get("Cookie", "")); item = cookie.get("zsm_session")
        return item.value if item else ""

    def _session(self) -> dict[str, object] | None:
        if not self.password: return NOAUTH_SESSION
        now = time.time()
        with SESSIONS_LOCK:
            for sid in [key for key, data in SESSIONS.items() if float(data.get("expires", 0)) < now]:
                SESSIONS.pop(sid, None)
            data = SESSIONS.get(self._session_id())
        return data if data and float(data.get("expires", 0)) >= now else None

    def _csrf(self) -> str:
        session = self._session(); return str(session.get("csrf", "")) if session else ""

    def _check_csrf(self, form: dict[str, str]) -> bool:
        return secrets.compare_digest(form.get("csrf", ""), self._csrf())

    def _require_login(self) -> bool:
        if self._session(): return True
        self._redirect("/login"); return False

    def _header(self) -> str:
        return '<header><div class="brand"><div class="logo">💾</div><div><h1>Zima Storage Manager</h1><div class="version">Gestione sicura dei nomi disco ZimaOS</div></div></div></header><nav><a href="/">Dischi</a><a href="/backups">Backup</a><a href="/history">Cronologia</a><a href="/diagnostics">Diagnostica</a><a href="/logout">Esci</a></nav>'

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health": self._send(b"OK", content_type="text/plain; charset=utf-8"); return
        if path == "/login": self._login_page(); return
        if path == "/logout":
            with SESSIONS_LOCK:
                SESSIONS.pop(self._session_id(), None)
            self._redirect("/login", {"Set-Cookie": "zsm_session=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0"}); return
        if not self._require_login(): return
        if path == "/": self._home()
        elif path == "/rename": self._rename_page()
        elif path == "/backups": self._backups_page()
        elif path == "/history": self._history_page()
        elif path == "/diagnostics": self._diagnostics_page()
        else: self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/login": self._login(); return
        if not self._require_login(): return
        try: form = self._form()
        except ValueError as exc: self._error(str(exc)); return
        if not self._check_csrf(form): self._error("Sessione o token di sicurezza non valido.", HTTPStatus.FORBIDDEN); return
        if path == "/confirm": self._confirm(form)
        elif path == "/apply": self._apply(form)
        elif path == "/backup/create": self._create_backup()
        elif path == "/backup/restore/confirm": self._restore_confirm(form)
        elif path == "/backup/restore": self._restore_backup(form)
        else: self.send_error(HTTPStatus.NOT_FOUND)

    def _login_page(self, error: str = "") -> None:
        if self._session(): self._redirect("/"); return
        box = f'<div class="card error"><strong>{esc(error)}</strong></div>' if error else ""
        body = '<header><div class="brand"><div class="logo">💾</div><div><h1>Zima Storage Manager</h1></div></div></header>' + box + '<form class="card" method="post" action="/login"><h2>Accesso</h2><p>Inserisci il codice mostrato al termine dell’installazione.</p><label>Codice di accesso</label><input name="password" type="password" autocomplete="current-password" required autofocus><button type="submit">Entra</button></form>'
        self._send(page("Accesso", body), HTTPStatus.UNAUTHORIZED if error else HTTPStatus.OK)

    def _login(self) -> None:
        supplied = self._form().get("password", "")
        if not self.password or secrets.compare_digest(supplied, self.password):
            sid = secrets.token_urlsafe(32)
            with SESSIONS_LOCK:
                SESSIONS[sid] = {"expires": time.time() + SESSION_TTL, "csrf": secrets.token_urlsafe(32)}
            cookie = f"zsm_session={sid}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}" + ("; Secure" if self.cookie_secure else "")
            self._redirect("/", {"Set-Cookie": cookie}); return
        time.sleep(.6); self._login_page("Codice non corretto.")

    def _home(self) -> None:
        try: disks = self.manager.disks()
        except Exception as exc: self._error(f"Impossibile leggere i dischi: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR); return
        cards = []
        for disk in disks:
            name = disk.label or Path(disk.mount_point).name or "Disco senza nome"
            badges = [disk.size or "Dimensione sconosciuta", (disk.fs_type or "filesystem sconosciuto").upper(), "Collegato" if disk.device else "Non collegato"]
            cards.append(f'<article class="card"><div class="disk-top"><div class="disk-icon">🗄️</div><div><div class="disk-name">{esc(name)}</div><div class="small">{esc(disk.device or "Dispositivo non rilevato")}</div></div></div><div class="meta">{"".join(f"<span class=badge>{esc(x)}</span>" for x in badges)}</div><p class="small"><code>{esc(disk.mount_point)}</code></p><a class="button" href="/rename?id={quote(disk.uuid)}">Cambia nome</a></article>')
        content = '<div class="grid">' + ''.join(cards) + '</div>' if cards else '<div class="card"><h2>Nessun disco disponibile</h2></div>'
        self._send(page("Dischi", self._header() + '<div class="card notice"><strong>Operazione protetta</strong><p class="small">Prima di ogni modifica viene creato un backup SQLite verificato.</p></div>' + content))

    def _rename_page(self) -> None:
        uuid = parse_qs(urlparse(self.path).query).get("id", [""])[0]
        try: disk = self.manager.db.get_by_uuid(uuid)
        except Exception as exc: self._error(str(exc)); return
        if not disk: self._error("Disco non trovato.", HTTPStatus.NOT_FOUND); return
        body = self._header() + f'<form class="card" method="post" action="/confirm"><h2>Cambia nome</h2><p>Nome attuale: <code>{esc(Path(disk.mount_point).name)}</code></p><label>Nuovo nome</label><input name="name" maxlength="64" required autofocus><input type="hidden" name="uuid" value="{esc(uuid)}"><input type="hidden" name="csrf" value="{esc(self._csrf())}"><div class="actions"><a class="button secondary" href="/">Annulla</a><button type="submit">Continua</button></div></form>'
        self._send(page("Cambia nome", body))

    def _confirm(self, form: dict[str, str]) -> None:
        uuid, name = form.get("uuid", ""), form.get("name", "").strip()
        try:
            disk = self.manager.db.get_by_uuid(uuid)
            if not disk: raise LookupError("Disco non trovato")
            name = validate_name(name)
        except Exception as exc: self._error(str(exc)); return
        nonce = secrets.token_urlsafe(18); proof = hashlib.sha256(f"{self._session_id()}:{uuid}:{name}:{nonce}".encode()).hexdigest()
        session = self._session(); session[f"confirm:{proof}"] = time.time() + CONFIRM_TTL
        body = self._header() + f'<form class="card notice" method="post" action="/apply"><h2>Conferma la modifica</h2><p><code>{esc(Path(disk.mount_point).name)}</code> → <code>{esc(name)}</code></p><input type="hidden" name="uuid" value="{esc(uuid)}"><input type="hidden" name="name" value="{esc(name)}"><input type="hidden" name="nonce" value="{esc(nonce)}"><input type="hidden" name="proof" value="{esc(proof)}"><input type="hidden" name="csrf" value="{esc(self._csrf())}"><div class="actions"><a class="button secondary" href="/">Annulla</a><button class="danger" type="submit">Conferma e rinomina</button></div></form>'
        self._send(page("Conferma", body))

    def _apply(self, form: dict[str, str]) -> None:
        uuid, name, nonce, proof = (form.get(x, "") for x in ("uuid", "name", "nonce", "proof"))
        expected = hashlib.sha256(f"{self._session_id()}:{uuid}:{name}:{nonce}".encode()).hexdigest()
        session = self._session(); deadline = float(session.pop(f"confirm:{proof}", 0))
        if not secrets.compare_digest(proof, expected) or deadline < time.time(): self._error("Conferma non valida o scaduta."); return
        try: result = self.manager.rename(uuid, name)
        except Exception as exc: self._error(f"Modifica non riuscita: {exc}"); return
        self._send(page("Completato", self._header() + f'<div class="card success"><h2>Nome modificato</h2><p>Nuovo percorso: <code>{esc(result["new"])}</code></p><a class="button" href="/">Fine</a></div>'))

    def _backups_page(self) -> None:
        try: backups = self.manager.backups()
        except Exception as exc: self._error(str(exc)); return
        rows = []
        for path in backups:
            stat = path.stat(); when = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
            rows.append(f'<div class="row"><div><strong>{esc(path.name)}</strong><div class="small">{esc(when)} · {stat.st_size/1024:.1f} KiB</div></div><form method="post" action="/backup/restore/confirm"><input type="hidden" name="backup" value="{esc(path.name)}"><input type="hidden" name="csrf" value="{esc(self._csrf())}"><button class="danger" type="submit">Ripristina</button></form></div>')
        content = ''.join(rows) if rows else '<p>Nessun backup disponibile.</p>'
        body = self._header() + f'<div class="card"><h2>Backup database</h2><form method="post" action="/backup/create"><input type="hidden" name="csrf" value="{esc(self._csrf())}"><button type="submit">Crea backup adesso</button></form></div><div class="card">{content}</div>'
        self._send(page("Backup", body))

    def _create_backup(self) -> None:
        try: path = self.manager.create_backup()
        except Exception as exc: self._error(f"Backup non riuscito: {exc}"); return
        self._send(page("Backup creato", self._header() + f'<div class="card success"><h2>Backup creato</h2><p><code>{esc(path.name)}</code></p><a class="button" href="/backups">Torna ai backup</a></div>'))

    def _restore_confirm(self, form: dict[str, str]) -> None:
        name = Path(form.get("backup", "")).name
        if not name or name != form.get("backup", ""):
            self._error("Nome backup non valido.")
            return
        path = self.config.backup_dir / name
        if not path.is_file():
            self._error("Backup non trovato.", HTTPStatus.NOT_FOUND)
            return
        nonce = secrets.token_urlsafe(18)
        proof = hashlib.sha256(f"{self._session_id()}:restore:{name}:{nonce}".encode()).hexdigest()
        session = self._session()
        session[f"restore:{proof}"] = time.time() + CONFIRM_TTL
        body = self._header() + f'<form class="card error" method="post" action="/backup/restore"><h2>Conferma ripristino</h2><p>Stai per sostituire il database attivo con:</p><p><code>{esc(name)}</code></p><p class="small">ZSM creerà prima un ulteriore backup di sicurezza.</p><input type="hidden" name="backup" value="{esc(name)}"><input type="hidden" name="nonce" value="{esc(nonce)}"><input type="hidden" name="proof" value="{esc(proof)}"><input type="hidden" name="csrf" value="{esc(self._csrf())}"><div class="actions"><a class="button secondary" href="/backups">Annulla</a><button class="danger" type="submit">Ripristina database</button></div></form>'
        self._send(page("Conferma ripristino", body))

    def _restore_backup(self, form: dict[str, str]) -> None:
        name = Path(form.get("backup", "")).name
        nonce, proof = form.get("nonce", ""), form.get("proof", "")
        expected = hashlib.sha256(f"{self._session_id()}:restore:{name}:{nonce}".encode()).hexdigest()
        session = self._session()
        deadline = float(session.pop(f"restore:{proof}", 0))
        if not secrets.compare_digest(proof, expected) or deadline < time.time():
            self._error("Conferma di ripristino non valida o scaduta.")
            return
        if not name or name != form.get("backup", ""):
            self._error("Nome backup non valido.")
            return
        try:
            self.manager.restore(self.config.backup_dir / name)
        except Exception as exc:
            self._error(f"Ripristino non riuscito: {exc}")
            return
        self._send(page("Ripristino completato", self._header() + '<div class="card success"><h2>Database ripristinato</h2><p>Il servizio di archiviazione è stato riavviato.</p><a class="button" href="/">Torna ai dischi</a></div>'))

    def _diagnostics_page(self) -> None:
        data = self.manager.diagnostics()
        state_class = "success" if data["database_ok"] else "error"
        roots = "".join(f"<li><code>{esc(root)}</code></li>" for root in data["mount_roots"])
        error = f'<p class="small">{esc(data["database_error"])}</p>' if data["database_error"] else ""
        body = self._header() + f'<div class="card {state_class}"><h2>Stato sistema</h2><div class="row"><span>Database</span><strong>{"OK" if data["database_ok"] else "ERRORE"}</strong></div><div class="row"><span>Servizio</span><strong>{esc(data["service"])}</strong></div><div class="row"><span>Backup disponibili</span><strong>{esc(data["backup_count"])}</strong></div>{error}</div><div class="card"><h2>Configurazione attiva</h2><p>Database: <code>{esc(data["database"])}</code></p><p>Servizio rilevato: <code>{esc(data["service_name"])}</code></p><p>Modalità: <code>{"Container ZimaOS" if data["container_mode"] else "Installazione nativa"}</code></p><p>Namespace host: <code>{"attivo" if data["host_namespace"] else "non attivo"}</code></p><p>Cartella backup: <code>{esc(data["backup_dir"])}</code></p><p>Radici di montaggio:</p><ul>{roots}</ul></div>'
        self._send(page("Diagnostica", body))

    def _history_page(self) -> None:
        rows = []
        for item in self.manager.history(100):
            details = item.get("details", {}); action = item.get("action", "evento"); status = item.get("status", "")
            rows.append(f'<div class="row"><div><strong>{esc(action)}</strong> <span class="badge">{esc(status)}</span><div class="small">{esc(item.get("timestamp", ""))}</div><div class="small"><code>{esc(details)}</code></div></div></div>')
        self._send(page("Cronologia", self._header() + '<div class="card"><h2>Cronologia operazioni</h2>' + (''.join(rows) or '<p>Nessuna operazione registrata.</p>') + '</div>'))

    def _error(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
        self._send(page("Errore", self._header() + f'<div class="card error"><h2>Operazione non riuscita</h2><p>{esc(message)}</p><a class="button secondary" href="/">Torna indietro</a></div>'), status)

    def log_message(self, format: str, *args) -> None: return


def main() -> None:
    host = os.environ.get("ZSM_HOST", "0.0.0.0"); port = int(os.environ.get("ZSM_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Zima Storage Manager v{APP_VERSION} attivo su http://{host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__": main()

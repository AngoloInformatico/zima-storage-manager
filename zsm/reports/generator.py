from __future__ import annotations
import html
import json
from datetime import datetime
from pathlib import Path
from ..models import AuditItem

def write_reports(items: list[AuditItem], directory: Path) -> dict[str, Path]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        directory = Path.home() / ".local/share/zsm/reports"
        directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    data = [item.to_dict() for item in items]
    json_path = directory / f"audit-{stamp}.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path = directory / f"audit-{stamp}.md"
    lines = ["# ZSM Audit Report", ""]
    for item in items:
        suffix = f" — _{item.recommendation}_" if item.recommendation else ""
        lines.append(f"- **{item.level.upper()} — {item.title}**: {item.detail}{suffix}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(item.level)}</td>"
        f"<td>{html.escape(item.title)}</td>"
        f"<td>{html.escape(item.detail)}</td>"
        f"<td>{html.escape(item.recommendation)}</td>"
        "</tr>"
        for item in items
    )
    html_doc = (
        "<!doctype html><html><head><meta charset='utf-8'><title>ZSM Audit</title>"
        "<style>body{font-family:system-ui;margin:2rem;background:#111827;color:#e5e7eb}"
        "table{width:100%;border-collapse:collapse}th,td{padding:.7rem;border-bottom:1px solid #374151;text-align:left}"
        "h1{color:#60a5fa}</style></head><body><h1>Zima Storage Manager Audit</h1>"
        f"<p>{datetime.now().isoformat(timespec='seconds')}</p>"
        "<table><tr><th>Level</th><th>Check</th><th>Detail</th><th>Recommendation</th></tr>"
        f"{rows}</table></body></html>"
    )
    html_path = directory / f"audit-{stamp}.html"
    html_path.write_text(html_doc, encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path, "html": html_path}

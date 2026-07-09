"""Dashboard API handlers for derez-company.

These module-level handler functions are referenced by dashboard/manifest.json.
Each receives HTTP request context and returns a JSON response.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Hermes adds the plugin root directory to sys.path,
# so we import from plugin-root-relative modules directly.
from discovery import ReportDiscovery
from markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)

_discovery: ReportDiscovery | None = None
_renderer: MarkdownRenderer | None = None
_reports_path: Path | None = None


def _ensure_initialized():
    global _discovery, _renderer, _reports_path
    if _discovery is not None:
        return
    _discovery = ReportDiscovery()
    _renderer = MarkdownRenderer()
    workspace = os.getcwd()
    _reports_path = Path(workspace) / "company" / "reports"
    _reports_path.mkdir(parents=True, exist_ok=True)
    _discovery.scan(_reports_path)
    logger.info("Company Dashboard initialized — scanning %s", _reports_path)


def _get_report(tab_id):
    _ensure_initialized()
    for r in _discovery.get_reports():
        if r.tab_id == tab_id:
            return r
    return None


def handle_tabs(request):
    _ensure_initialized()
    return {
        "tabs": [
            {
                "id": r.tab_id,
                "name": r.display_name,
                "path": str(r.path),
                "url": f"/dashboard/company/{r.tab_id}",
                "updated": r.mtime,
            }
            for r in _discovery.get_reports()
        ]
    }


def handle_report(request, tab_id):
    _ensure_initialized()
    report = _get_report(tab_id)
    if not report:
        return {"error": True, "message": f"Report '{tab_id}' not found"}
    if not report.path.exists():
        _discovery.scan(_reports_path)
        return {"error": True, "message": f"Report file '{report.path}' not found", "retry": True}
    try:
        content = report.path.read_text(encoding="utf-8")
        rendered = _renderer.render(content, tab_id)
        return {"tab_id": tab_id, "name": report.display_name, "path": str(report.path), "content": rendered}
    except Exception as exc:
        logger.error("Failed to read report %s: %s", report.path, exc)
        return {"error": True, "message": f"Failed to read {report.path.name}: {exc}", "retry": True}


def handle_toc(request, tab_id):
    _ensure_initialized()
    report = _get_report(tab_id)
    if not report or not report.path.exists():
        return {"headings": []}
    try:
        content = report.path.read_text(encoding="utf-8")
        return {"tab_id": tab_id, "headings": _renderer.extract_headings(content)}
    except Exception:
        return {"headings": []}


def handle_scan(request):
    _ensure_initialized()
    reports = _discovery.scan(_reports_path)
    return {
        "scanned": True,
        "count": len(reports),
        "tabs": [{"id": r.tab_id, "name": r.display_name} for r in reports],
    }


def handle_search(request):
    _ensure_initialized()
    query = request.args.get("q", "") if hasattr(request, "args") else ""
    if not query:
        return handle_tabs(request)
    query_lower = query.lower()
    results = []
    for r in _discovery.get_reports():
        if query_lower in r.display_name.lower():
            results.append({"id": r.tab_id, "name": r.display_name, "match": "name"})
            continue
        try:
            content = r.path.read_text(encoding="utf-8")
            matching = [l.strip() for l in content.splitlines() if query_lower in l.lower()]
            if matching:
                results.append({"id": r.tab_id, "name": r.display_name, "match": "content", "matches": matching[:5]})
        except Exception:
            pass
    return {"results": results, "query": query}
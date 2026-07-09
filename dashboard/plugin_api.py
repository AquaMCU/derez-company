"""Company Reports Dashboard — Hermes plugin API.

FastAPI APIRouter mounted by the Hermes dashboard at runtime.
Provides the backend endpoints for the Company reports tab.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from discovery import ReportDiscovery
from markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)

router = APIRouter(tags=["derez-company"])

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


@router.get("/tabs")
async def get_tabs():
    _ensure_initialized()
    return [
        {
            "id": r.tab_id,
            "name": r.display_name,
            "path": str(r.path),
            "url": f"/dashboard/company/{r.tab_id}",
            "updated": r.mtime,
        }
        for r in _discovery.get_reports()
    ]


@router.get("/report/{tab_id}")
async def get_report(tab_id: str):
    _ensure_initialized()
    report = _get_report(tab_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{tab_id}' not found")
    if not report.path.exists():
        _discovery.scan(_reports_path)
        raise HTTPException(status_code=404, detail=f"Report file '{report.path}' not found")

    try:
        content = report.path.read_text(encoding="utf-8")
        rendered = _renderer.render(content, tab_id)
        return {
            "tab_id": tab_id,
            "name": report.display_name,
            "path": str(report.path),
            "content": rendered,
        }
    except Exception as exc:
        logger.error("Failed to read report %s: %s", report.path, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/toc/{tab_id}")
async def get_toc(tab_id: str):
    _ensure_initialized()
    report = _get_report(tab_id)
    if not report or not report.path.exists():
        return {"headings": []}
    try:
        content = report.path.read_text(encoding="utf-8")
        return {"tab_id": tab_id, "headings": _renderer.extract_headings(content)}
    except Exception:
        return {"headings": []}


@router.post("/scan")
async def rescan():
    _ensure_initialized()
    reports = _discovery.scan(_reports_path)
    return {
        "scanned": True,
        "count": len(reports),
        "tabs": [{"id": r.tab_id, "name": r.display_name} for r in reports],
    }


@router.get("/search")
async def search(q: str = ""):
    _ensure_initialized()
    if not q:
        return await get_tabs()
    q_lower = q.lower()
    results = []
    for r in _discovery.get_reports():
        if q_lower in r.display_name.lower():
            results.append({"id": r.tab_id, "name": r.display_name, "match": "name"})
            continue
        try:
            content = r.path.read_text(encoding="utf-8")
            matching = [l.strip() for l in content.splitlines() if q_lower in l.lower()]
            if matching:
                results.append({"id": r.tab_id, "name": r.display_name, "match": "content", "matches": matching[:5]})
        except Exception:
            pass
    return {"results": results, "query": q}
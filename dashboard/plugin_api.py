"""Company Reports Dashboard — Hermes plugin API.

FastAPI APIRouter mounted by the Hermes dashboard at runtime.
Provides the backend endpoints for the Company reports tab.

State is initialized by __init__.py's register() and shared via
the _plugin_state module attribute.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Ensure plugin root is on sys.path for sibling imports
_plugin_root = str(Path(__file__).resolve().parent.parent)
if _plugin_root not in sys.path:
    sys.path.insert(0, _plugin_root)

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["derez-company"])

# State set by __init__.py register()
_plugin_state = None


def _get_state():
    """Return the shared plugin state initialized by register()."""
    global _plugin_state
    if _plugin_state is not None:
        return _plugin_state
    # Fallback: initialize independently if register() hasn't run yet
    from discovery import ReportDiscovery
    from markdown_renderer import MarkdownRenderer
    discovery = ReportDiscovery()
    renderer = MarkdownRenderer()
    workspace = os.getcwd()
    reports_path = Path(workspace) / "company" / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)
    discovery.scan(reports_path)
    _plugin_state = {
        "discovery": discovery,
        "renderer": renderer,
        "reports_path": reports_path,
    }
    logger.info("Company Dashboard initialized (fallback) — scanning %s", reports_path)
    return _plugin_state


@router.get("/tabs")
async def get_tabs():
    state = _get_state()
    discovery = state["discovery"]
    return [
        {
            "id": r.tab_id,
            "name": r.display_name,
            "path": str(r.path),
            "url": f"/dashboard/company/{r.tab_id}",
            "updated": r.mtime,
        }
        for r in discovery.get_reports()
    ]


@router.get("/report/{tab_id}")
async def get_report(tab_id: str):
    state = _get_state()
    discovery = state["discovery"]
    renderer = state["renderer"]
    reports_path = state["reports_path"]

    report = discovery.get_report(tab_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{tab_id}' not found")
    if not report.path.exists():
        discovery.scan(reports_path)
        raise HTTPException(status_code=404, detail=f"Report file not found")

    try:
        content = report.path.read_text(encoding="utf-8")
        rendered = renderer.render(content, tab_id)
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
    state = _get_state()
    discovery = state["discovery"]
    renderer = state["renderer"]

    report = discovery.get_report(tab_id)
    if not report or not report.path.exists():
        return {"headings": []}
    try:
        content = report.path.read_text(encoding="utf-8")
        return {"tab_id": tab_id, "headings": renderer.extract_headings(content)}
    except Exception:
        return {"headings": []}


@router.post("/scan")
async def rescan():
    state = _get_state()
    discovery = state["discovery"]
    reports_path = state["reports_path"]

    reports = discovery.scan(reports_path)
    return {
        "scanned": True,
        "count": len(reports),
        "tabs": [{"id": r.tab_id, "name": r.display_name} for r in reports],
    }


@router.get("/search")
async def search(q: str = ""):
    state = _get_state()
    discovery = state["discovery"]

    if not q:
        return await get_tabs()
    q_lower = q.lower()
    results = []
    for r in discovery.get_reports():
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
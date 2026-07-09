"""derez-company — Hermes plugin.

Bundles:
- derez-crm skill (data management for leads, funnel, config)
- derez-dashboard skill (company reports dashboard specification)
- Company Reports Dashboard tab (auto-discovers and renders reports)
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def register(ctx):
    """Register the derez-company plugin with Hermes."""

    # --- Bundle skills so they're recognized by Hermes ---
    plugin_dir = Path(__file__).parent

    skills_dir = plugin_dir / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                skill_name = skill_dir.name
                ctx.register_skill(name=skill_name, path=str(skill_dir))
                logger.info("Registered bundled skill: %s", skill_name)

    # --- Dashboard: resolve reports path ---
    workspace = getattr(ctx, "workspace", None) or os.getcwd()
    reports_path = Path(workspace) / "company" / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)

    # Lazy imports for dashboard — avoids pulling heavy deps at module level
    from .discovery import ReportDiscovery
    from .markdown_renderer import MarkdownRenderer

    discovery = ReportDiscovery()
    renderer = MarkdownRenderer()
    discovery.scan(reports_path)

    # --- Internal helpers ---

    def _get_report(tab_id):
        for r in discovery.get_reports():
            if r.tab_id == tab_id:
                return r
        return None

    def _tabs():
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

    def _report(tab_id):
        report = _get_report(tab_id)
        if not report:
            return {"error": True, "message": f"Report '{tab_id}' not found"}
        if not report.path.exists():
            discovery.scan(reports_path)
            return {
                "error": True,
                "message": f"Report file '{report.path}' not found",
                "retry": True,
            }
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
            return {
                "error": True,
                "message": f"Failed to read {report.path.name}: {exc}",
                "retry": True,
            }

    def _toc(tab_id):
        report = _get_report(tab_id)
        if not report or not report.path.exists():
            return {"headings": []}
        try:
            content = report.path.read_text(encoding="utf-8")
            return {"tab_id": tab_id, "headings": renderer.extract_headings(content)}
        except Exception:
            return {"headings": []}

    def _scan():
        reports = discovery.scan(reports_path)
        return {
            "scanned": True,
            "count": len(reports),
            "tabs": [{"id": r.tab_id, "name": r.display_name} for r in reports],
        }

    def _search(query):
        if not query:
            return _tabs()
        reports = discovery.get_reports()
        query_lower = query.lower()
        results = []
        for r in reports:
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
        return results

    # --- Hook: refresh index when reports are written ---
    def _on_tool_call(tool_name, params, result):
        if tool_name in ("write_file", "patch", "file_write", "edit_file"):
            path_str = str(params.get("path", "")) if isinstance(params, dict) else ""
            if "company/reports" in path_str or str(reports_path) in path_str:
                discovery.scan(reports_path)

    ctx.register_hook("post_tool_call", _on_tool_call)

    # --- Slash command ---
    def _cmd_reports(params):
        args = (params or "").strip() if isinstance(params, str) else ""
        if not args:
            tabs = _tabs()
            if not tabs:
                return "No company reports found. Add markdown files to `company/reports/`."
            lines = ["**Company Reports:**"]
            for t in tabs:
                lines.append(f"  · `{t['id']}` — {t['name']}")
            return "\n".join(lines)
        tab_id = args.split()[0]
        report = _get_report(tab_id)
        if not report:
            return f"Report '{tab_id}' not found. Use `/reports` to list available reports."
        try:
            lines = report.path.read_text(encoding="utf-8").splitlines()
            return f"**{report.display_name}**\n\n" + "\n".join(lines[:20])
        except Exception as exc:
            return f"Error reading {report.display_name}: {exc}"

    ctx.register_command(
        name="reports",
        handler=_cmd_reports,
        description="List company reports and view summaries. Usage: /reports [tab_id]",
    )

    logger.info(
        "derez-company initialized — %d skills bundled, scanning %s",
        len(list(skills_dir.iterdir())) if skills_dir.exists() else 0,
        reports_path,
    )
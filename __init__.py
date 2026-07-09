"""derez-company — Hermes plugin.

Bundles:
- derez-crm skill (data management for leads, funnel, config)
- derez-dashboard skill (company reports dashboard specification)
- Company Reports Dashboard tab (auto-discovers and renders reports)
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def register(ctx):
    """Register the derez-company plugin with Hermes."""

    # Ensure plugin root is on sys.path for sibling imports
    _plugin_root = str(Path(__file__).parent.resolve())
    if _plugin_root not in sys.path:
        sys.path.insert(0, _plugin_root)

    # --- Bundle skills ---
    skills_dir = Path(_plugin_root) / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                ctx.register_skill(name=skill_dir.name, path=str(skill_dir))
                logger.info("Registered bundled skill: %s", skill_dir.name)

    # --- Dashboard: resolve reports path ---
    workspace = getattr(ctx, "workspace", None) or str(Path.home())
    reports_path = Path(workspace) / "company" / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)

    # Absolute imports (sibling modules)
    from discovery import ReportDiscovery
    from markdown_renderer import MarkdownRenderer

    discovery = ReportDiscovery()
    renderer = MarkdownRenderer()
    discovery.scan(reports_path)

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
            reports = discovery.get_reports()
            if not reports:
                return "No company reports found. Add markdown files to `company/reports/`."
            lines = ["**Company Reports:**"]
            for r in reports:
                lines.append(f"  · `{r.tab_id}` — {r.display_name}")
            return "\n".join(lines)
        tab_id = args.split()[0]
        report = discovery.get_report(tab_id)
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

    # --- Store state for the dashboard API (plugin_api.py) ---
    # Hermes calls register() before mounting the API routes,
    # so plugin_api.py can pick up pre-initialized state.
    _state = {
        "discovery": discovery,
        "renderer": renderer,
        "reports_path": reports_path,
    }
    # Expose on the module so plugin_api.py can access it
    import dashboard.plugin_api as api_mod
    api_mod._plugin_state = _state

    logger.info(
        "derez-company initialized — scanning %s",
        reports_path,
    )
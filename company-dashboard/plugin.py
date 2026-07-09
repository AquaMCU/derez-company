# company-dashboard plugin for Hermes
#
# Auto-discovers markdown reports in company/reports/ and exposes each as
# a dashboard tab under the "Company" dashboard group.
#
# Plugin ID: company-dashboard
# Dashboard label: Company
#
# Install: place this directory at ~/.hermes/plugins/company-dashboard/
# or at <hermes-repo>/plugins/company-dashboard/ (bundled).
#
# The dashboard/manifest.json auto-registers the Company tab — no
# plugins.enabled config needed for dashboard-only plugins.

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from hermes.plugin import HermesPlugin
from hermes.dashboard import DashboardTab, DashboardProvider

from .discovery import ReportDiscovery
from .markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)


class CompanyDashboardPlugin(HermesPlugin):
    """Hermes dashboard plugin that renders company reports as tabs."""

    name = "company-dashboard"
    display_name = "Company Reports Dashboard"
    description = "Auto-discovers markdown reports in company/reports/ and renders them as dashboard tabs"

    def __init__(self, hermes: Any) -> None:
        super().__init__(hermes)
        self._discovery = ReportDiscovery()
        self._renderer = MarkdownRenderer()
        self._reports_path: Path | None = None
        self._watch_active = False

    def on_init(self) -> None:
        """Initialize the plugin: resolve reports path, scan for reports."""
        config = self.config or {}
        reports_rel = config.get("reports_path", "company/reports")

        # Resolve the reports path relative to the Hermes workspace
        workspace = getattr(self.hermes, "workspace", None) or os.getcwd()
        self._reports_path = Path(workspace) / reports_rel
        self._reports_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Company Dashboard initialized, scanning: %s", self._reports_path
        )

        # Register as a dashboard provider
        self.hermes.dashboard.register_provider(
            DashboardProvider(
                id="company",
                name="Company",
                icon="building",
                priority=10,
                plugin=self,
            )
        )

        # Initial scan
        self._discovery.scan(self._reports_path)

        # Watch for file changes (if Hermes supports file watching)
        self._start_watcher()

    def on_shutdown(self) -> None:
        """Clean up watcher on shutdown."""
        self._stop_watcher()

    def get_dashboard_tabs(self) -> list[DashboardTab]:
        """Return all discovered report tabs."""
        reports = self._discovery.get_reports()
        if not reports:
            return []

        tabs = []
        for report in reports:
            tab_id = report["tab_id"]
            tabs.append(
                DashboardTab(
                    id=tab_id,
                    name=report["display_name"],
                    group="Company",
                    route=f"/dashboard/company/{tab_id}",
                    plugin=self,
                )
            )
        return tabs

    def get_route(self, route_name: str, **params: Any) -> Any:
        """Handle dashboard route requests."""
        if route_name == "tabs":
            return self._handle_tabs()
        elif route_name == "report":
            return self._handle_report(params.get("tab_id", ""))
        elif route_name == "scan":
            return self._handle_scan()
        elif route_name == "toc":
            return self._handle_toc(params.get("tab_id", ""))
        return None

    def _handle_tabs(self) -> dict:
        """Return list of available tabs with metadata."""
        reports = self._discovery.get_reports()
        tabs = []
        for report in reports:
            tabs.append({
                "id": report["tab_id"],
                "name": report["display_name"],
                "path": str(report["path"]),
                "url": f"/dashboard/company/{report['tab_id']}",
                "updated": report.get("mtime", ""),
            })
        return {"tabs": tabs}

    def _handle_report(self, tab_id: str) -> dict:
        """Render a single report by tab_id."""
        reports = self._discovery.get_reports()
        report = next((r for r in reports if r["tab_id"] == tab_id), None)
        if not report:
            return self._error_response(f"Report '{tab_id}' not found", 404)

        path = report["path"]
        if not path.exists():
            self._discovery.scan(self._reports_path)
            return self._error_response(f"Report file '{path}' not found", 404)

        try:
            content = path.read_text(encoding="utf-8")
            rendered = self._renderer.render(content, tab_id)
            return {
                "tab_id": tab_id,
                "name": report["display_name"],
                "path": str(path),
                "content": rendered,
            }
        except Exception as exc:
            logger.error("Failed to read report %s: %s", path, exc)
            return self._error_response(
                f"Failed to read {path.name}: {exc}", 500, retry=True
            )

    def _handle_scan(self) -> dict:
        """Force a rescan of the reports directory."""
        if self._reports_path:
            reports = self._discovery.scan(self._reports_path)
            return {
                "scanned": True,
                "count": len(reports),
                "tabs": [
                    {
                        "id": r["tab_id"],
                        "name": r["display_name"],
                    }
                    for r in reports
                ],
            }
        return {"scanned": False, "count": 0, "tabs": []}

    def _handle_toc(self, tab_id: str) -> dict:
        """Return the table of contents for a report."""
        reports = self._discovery.get_reports()
        report = next((r for r in reports if r["tab_id"] == tab_id), None)
        if not report or not report["path"].exists():
            return {"headings": []}

        try:
            content = report["path"].read_text(encoding="utf-8")
            headings = self._renderer.extract_headings(content)
            return {"tab_id": tab_id, "headings": headings}
        except Exception:
            return {"headings": []}

    def _error_response(
        self, message: str, status: int = 500, retry: bool = False
    ) -> dict:
        """Return a standardized error response."""
        resp: dict[str, Any] = {
            "error": True,
            "message": message,
            "status": status,
        }
        if retry:
            resp["retry"] = True
        return resp

    def _start_watcher(self) -> None:
        """Start a file watcher on the reports directory if Hermes supports it."""
        try:
            from hermes.utils.file_watcher import FileWatcher

            self._watcher = FileWatcher(
                str(self._reports_path),
                patterns=["*.md"],
                on_change=self._on_report_change,
            )
            self._watcher.start()
            self._watch_active = True
            logger.debug("File watcher started on %s", self._reports_path)
        except ImportError:
            logger.debug("FileWatcher not available — polling-based refresh")
            self._watch_active = False
        except Exception as exc:
            logger.warning("Failed to start file watcher: %s", exc)
            self._watch_active = False

    def _stop_watcher(self) -> None:
        """Stop the file watcher if active."""
        if self._watch_active and hasattr(self, "_watcher"):
            try:
                self._watcher.stop()
            except Exception:
                pass
            self._watch_active = False

    def _on_report_change(self, path: str) -> None:
        """Handle a report file change event."""
        logger.debug("Report change detected: %s", path)
        if self._reports_path:
            self._discovery.scan(self._reports_path)
            # Notify the dashboard to refresh
            try:
                self.hermes.dashboard.refresh_tab_group("Company")
            except Exception:
                pass


# Hermes plugin discovery hook
def create_plugin(hermes: Any) -> HermesPlugin:
    return CompanyDashboardPlugin(hermes)
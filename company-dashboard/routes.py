"""Company Dashboard API routes for Hermes.

Handles tab listing, report content fetching, search, and table of contents.
"""

from __future__ import annotations

import logging
from pathlib import Path

from hermes.plugin import route
from hermes.dashboard import DashboardRoute

from .plugin import CompanyDashboardPlugin

logger = logging.getLogger(__name__)


def register_routes(plugin: CompanyDashboardPlugin) -> list[DashboardRoute]:
    """Register dashboard routes for the Company plugin."""
    return [
        DashboardRoute(
            path="/api/plugins/company-dashboard/tabs",
            handler=plugin._handle_tabs,
            methods=["GET"],
        ),
        DashboardRoute(
            path="/api/plugins/company-dashboard/report/{tab_id}",
            handler=plugin._handle_report,
            methods=["GET"],
        ),
        DashboardRoute(
            path="/api/plugins/company-dashboard/toc/{tab_id}",
            handler=plugin._handle_toc,
            methods=["GET"],
        ),
        DashboardRoute(
            path="/api/plugins/company-dashboard/scan",
            handler=plugin._handle_scan,
            methods=["POST"],
        ),
    ]
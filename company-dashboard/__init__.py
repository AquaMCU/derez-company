"""company-dashboard plugin initialization.

Package metadata for the Hermes dashboard plugin.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__plugin_name__ = "company-dashboard"
__plugin_description__ = (
    "Company Reports Dashboard — auto-discovers and renders "
    "markdown reports from company/reports/"
)

from .plugin import CompanyDashboardPlugin, create_plugin

__all__ = ["CompanyDashboardPlugin", "create_plugin"]
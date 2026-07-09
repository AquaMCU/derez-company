"""Report discovery — scans company/reports/ for markdown files and indexes them."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Known acronyms that should remain uppercase in display names
KNOWN_ACRONYMS: set[str] = {
    "CRM", "ERP", "API", "AI", "HR", "KPI", "OKR", "SaaS",
    "PDF", "HTML", "CSS", "JS", "TS", "JSON", "YAML", "CLI",
    "UI", "UX", "SSH", "HTTP", "HTTPS", "URL", "URI", "DNS",
    "DB", "SQL", "AI", "ML", "LLM", "ID", "TLS", "SSL",
}


@dataclass
class ReportInfo:
    """Information about a discovered report."""

    tab_id: str
    display_name: str
    path: Path
    filename: str
    mtime: float


class ReportDiscovery:
    """Scans a directory for markdown reports and maintains an index.

    The index maps tab_id -> ReportInfo.
    Hidden files (dot-prefixed) are ignored.
    Results are sorted alphabetically by display_name.
    """

    def __init__(self) -> None:
        self._reports: dict[str, ReportInfo] = {}

    def scan(self, directory: Path) -> list[ReportInfo]:
        """Scan the directory for .md files and rebuild the index.

        Args:
            directory: Path to the reports directory.

        Returns:
            Sorted list of ReportInfo objects.
        """
        self._reports = {}
        if not directory.exists():
            logger.warning("Reports directory does not exist: %s", directory)
            return []

        for entry in sorted(directory.iterdir()):
            if not entry.is_file():
                continue
            if entry.name.startswith("."):
                continue
            if entry.suffix.lower() not in (".md", ".mdx"):
                continue

            report = self._build_report(entry)
            self._reports[report.tab_id] = report

        logger.debug(
            "Scanned %s — found %d reports", directory, len(self._reports)
        )
        return self.get_reports()

    def get_reports(self) -> list[ReportInfo]:
        """Return all discovered reports sorted by display name."""
        return sorted(
            self._reports.values(), key=lambda r: r.display_name.lower()
        )

    def get_report(self, tab_id: str) -> ReportInfo | None:
        """Get a single report by its tab_id."""
        return self._reports.get(tab_id)

    def get_tab_ids(self) -> list[str]:
        """Return all tab IDs."""
        return list(self._reports.keys())

    def count(self) -> int:
        """Return the number of discovered reports."""
        return len(self._reports)

    @staticmethod
    def _build_report(path: Path) -> ReportInfo:
        """Build a ReportInfo from a file path.

        Converts the filename (without extension) into:
        - tab_id: kebab-case slug
        - display_name: Title Case with known acronyms preserved
        """
        stem = path.stem  # filename without extension
        tab_id = _to_kebab(stem)
        display_name = _to_display_name(stem)

        mtime = path.stat().st_mtime if path.exists() else 0.0

        return ReportInfo(
            tab_id=tab_id,
            display_name=display_name,
            path=path,
            filename=path.name,
            mtime=mtime,
        )


def _to_kebab(name: str) -> str:
    """Convert a filename stem to kebab-case.

    Examples:
        crm -> crm
        sales_pipeline -> sales-pipeline
        customerSuccess -> customer-success
        Customer Success -> customer-success
    """
    # Replace underscores and spaces with hyphens
    name = re.sub(r"[\s_]+", "-", name)
    # Insert hyphens before uppercase letters (camelCase -> camel-case)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    # Insert hyphens between consecutive uppercase and lowercase (PDFReport -> pdf-report)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    return name.lower()


def _to_display_name(name: str) -> str:
    """Convert a filename stem to a display name (Title Case with acronyms).

    Examples:
        crm -> CRM
        sales_pipeline -> Sales Pipeline
        customer-success -> Customer Success
        sales_pipeline_report -> Sales Pipeline Report
        api_usage -> API Usage
    """
    # Split on underscores, hyphens, spaces, and camelCase boundaries
    parts = re.split(r"[-_\s]+", name)

    # Also split camelCase within each part
    split_parts: list[str] = []
    for part in parts:
        sub = re.split(
            r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", part
        )
        split_parts.extend(sub)

    # Title case each word, except known acronyms
    result_parts: list[str] = []
    for word in split_parts:
        if not word:
            continue
        upper = word.upper()
        if upper in KNOWN_ACRONYMS:
            result_parts.append(upper)
        else:
            result_parts.append(word[0].upper() + word[1:].lower())

    return " ".join(result_parts)

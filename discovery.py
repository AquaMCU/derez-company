"""Report discovery — scans company/reports/ for markdown files and indexes them."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

KNOWN_ACRONYMS: set[str] = {
    "CRM", "ERP", "API", "AI", "HR", "KPI", "OKR", "SaaS",
    "PDF", "HTML", "CSS", "JS", "TS", "JSON", "YAML", "CLI",
    "UI", "UX", "SSH", "HTTP", "HTTPS", "URL", "URI", "DNS",
    "DB", "SQL", "ML", "LLM", "ID", "TLS", "SSL",
}


@dataclass
class ReportInfo:
    tab_id: str
    display_name: str
    path: Path
    filename: str
    mtime: float


class ReportDiscovery:
    """Scans a directory for markdown reports and maintains an index."""

    def __init__(self) -> None:
        self._reports: dict[str, ReportInfo] = {}

    def scan(self, directory: Path) -> list[ReportInfo]:
        self._reports = {}
        if not directory.exists():
            logger.warning("Reports directory does not exist: %s", directory)
            return []

        for entry in sorted(directory.iterdir()):
            if not entry.is_file() or entry.name.startswith("."):
                continue
            if entry.suffix.lower() not in (".md", ".mdx", ".html"):
                continue
            report = self._build_report(entry)
            tab_id = report.tab_id
            # Prefer .html over .md/.mdx when both exist with the same tab_id
            existing = self._reports.get(tab_id)
            if existing and existing.path.suffix.lower() == ".html":
                continue  # keep the existing .html
            if existing and report.path.suffix.lower() == ".html":
                self._reports[tab_id] = report  # upgrade to .html
            else:
                self._reports[tab_id] = report

        logger.debug("Scanned %s — found %d reports", directory, len(self._reports))
        return self.get_reports()

    def get_reports(self) -> list[ReportInfo]:
        return sorted(self._reports.values(), key=lambda r: r.display_name.lower())

    def get_report(self, tab_id: str) -> ReportInfo | None:
        return self._reports.get(tab_id)

    def get_tab_ids(self) -> list[str]:
        return list(self._reports.keys())

    def count(self) -> int:
        return len(self._reports)

    @staticmethod
    def _build_report(path: Path) -> ReportInfo:
        stem = path.stem
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
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    return name.lower()


def _to_display_name(name: str) -> str:
    parts = re.split(r"[-_\s]+", name)
    split_parts: list[str] = []
    for part in parts:
        sub = re.split(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", part)
        split_parts.extend(sub)
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
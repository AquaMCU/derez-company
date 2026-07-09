"""Markdown rendering and enhancement for the Company dashboard.

Parses raw markdown into a structured, enhanced representation suitable for
rendering with Hermes UI primitives. Performs automatic enhancement: metrics
become metric cards, statuses become badges, callouts become alerts, etc.
"""

from __future__ import annotations

import re
from typing import Any


class MarkdownRenderer:
    """Renders markdown content with automatic presentation enhancements.

    Preserves all markdown structure while promoting metrics, statuses,
    callouts, tables, and lists into richer UI components.
    """

    # Regex to detect metric lines: "Label: value" where value looks numeric
    _METRIC_RE = re.compile(
        r"^\s*([\w\s]+?)\s*:\s*"
        r"([\$€£]?\s*[\d,]+(?:\.\d+)?[%x]?\s*(?:[KMBkmb])?"
        r"|[A-Z]+\$\s*[\d,]+(?:\.\d+)?[MB]?)"
        r"\s*$"
    )

    # Status words that should be rendered as badges
    _STATUSES = {
        "active", "blocked", "delayed", "done", "critical",
        "warning", "success", "failed", "pending", "in progress",
        "complete", "cancelled", "on hold", "approved", "rejected",
        "cold", "warm", "hot", "won", "lost", "blacklisted",
    }

    # Callout prefixes
    _CALLOUTS = {
        "note", "warning", "important", "todo",
        "info", "tip", "caution", "danger",
    }

    def render(self, markdown: str, tab_id: str) -> dict:
        """Render markdown content into an enhanced structure.

        Args:
            markdown: Raw markdown string.
            tab_id: Identifier for the report tab.

        Returns:
            A dict with the rendered structure:
            {
                "sections": [...],    # enhanced markdown sections
                "metrics": [...],     # promoted metric cards
                "headings": [...],    # extracted table of contents
                "raw_html": str,      # HTML rendering of markdown
            }
        """
        sections = self._split_sections(markdown)
        metrics = self._extract_metrics(markdown)
        headings = self.extract_headings(markdown)
        raw_html = self._to_html(markdown)

        enhanced_sections = []
        for section in sections:
            enhanced_sections.append(self._enhance_section(section))

        return {
            "sections": enhanced_sections,
            "metrics": metrics,
            "headings": headings,
            "raw_html": raw_html,
            "word_count": len(markdown.split()),
        }

    def extract_headings(self, markdown: str) -> list[dict]:
        """Extract a table of contents from markdown headings."""
        headings = []
        for line in markdown.splitlines():
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                anchor = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
                anchor = re.sub(r"[\s]+", "-", anchor)
                headings.append({
                    "level": level,
                    "text": text,
                    "anchor": anchor,
                })
        return headings

    def _split_sections(self, markdown: str) -> list[dict]:
        """Split markdown into sections by headings."""
        lines = markdown.splitlines()
        sections: list[dict] = []
        current: dict[str, Any] = {"heading": None, "level": 0, "body": []}

        for line in lines:
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                if current["body"] or current["heading"]:
                    current["body"] = "\n".join(current["body"]).strip()
                    sections.append(current)
                level = len(match.group(1))
                text = match.group(2).strip()
                anchor = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
                anchor = re.sub(r"[\s]+", "-", anchor)
                current = {
                    "heading": text,
                    "level": level,
                    "anchor": anchor,
                    "body": [],
                }
            else:
                current["body"].append(line)

        # Last section
        if current["heading"] or current["body"]:
            current["body"] = "\n".join(current["body"]).strip()
            sections.append(current)

        return sections

    def _enhance_section(self, section: dict) -> dict:
        """Enhance a section with automatic component detection."""
        body = section.get("body", "")
        enhanced: dict[str, Any] = {
            "heading": section.get("heading"),
            "level": section.get("level", 0),
            "anchor": section.get("anchor"),
            "type": self._detect_section_type(body),
            "body_html": self._to_html(body),
            "elements": self._parse_elements(body),
        }
        return enhanced

    def _detect_section_type(self, body: str) -> str:
        """Detect the type of content in a section."""
        lines = [l.strip() for l in body.splitlines() if l.strip()]

        if not lines:
            return "empty"

        # Check if it's a table
        if any(l.startswith("|") and l.endswith("|") for l in lines):
            pipe_count = sum(1 for l in lines if l.startswith("|"))
            if pipe_count >= 2:  # header + separator + data
                return "table"

        # Check if it's mostly metrics
        metric_lines = sum(
            1 for l in lines if self._METRIC_RE.match(l)
        )
        if len(lines) > 0 and metric_lines / len(lines) > 0.4:
            return "metrics"

        # Check if it's a list
        if any(
            l.startswith(("- ", "* ", "+ ", "1. "))
            for l in lines
        ):
            list_lines = sum(
                1 for l in lines
                if re.match(r"^[\s]*[-*+\d\.]+\s", l)
            )
            if len(lines) > 0 and list_lines / len(lines) > 0.5:
                return "list"

        return "markdown"

    def _parse_elements(self, body: str) -> list[dict]:
        """Parse body into individual UI elements."""
        elements: list[dict] = []
        lines = body.splitlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # Check for status badges
            lower = line.lower().strip(":*")
            if lower in self._STATUSES and len(line) < 30:
                elements.append({
                    "type": "status",
                    "text": line.strip("*:").strip(),
                    "value": lower,
                })
                i += 1
                continue

            # Check for callouts
            if lower in self._CALLOUTS and line.endswith(":"):
                callout_lines = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    callout_lines.append(lines[i].strip())
                    i += 1
                elements.append({
                    "type": "callout",
                    "variant": lower,
                    "text": " ".join(callout_lines),
                })
                continue

            # Check for metrics
            metric_match = self._METRIC_RE.match(line)
            if metric_match:
                label = metric_match.group(1).strip()
                value = metric_match.group(2).strip()
                elements.append({
                    "type": "metric",
                    "label": label,
                    "value": value,
                })
                i += 1
                continue

            # Check for list items
            list_match = re.match(r"^[\s]*[-*+\d\.]+\s+(.+)$", line)
            if list_match:
                items = []
                while i < len(lines):
                    item_match = re.match(
                        r"^[\s]*[-*+\d\.]+\s+(.+)$", lines[i].strip()
                    )
                    if item_match:
                        items.append({
                            "text": item_match.group(1),
                            "html": self._to_html(item_match.group(1)),
                        })
                        i += 1
                    else:
                        break
                elements.append({"type": "list_items", "items": items})
                continue

            # Default: inline markdown
            elements.append({
                "type": "text",
                "text": line,
                "html": self._to_html(line),
            })
            i += 1

        return elements

    def _extract_metrics(self, markdown: str) -> list[dict]:
        """Extract all metric-like lines as metric cards."""
        metrics = []
        for line in markdown.splitlines():
            match = self._METRIC_RE.match(line.strip())
            if match:
                metrics.append({
                    "label": match.group(1).strip(),
                    "value": match.group(2).strip(),
                })
        return metrics

    def _to_html(self, markdown: str) -> str:
        """Convert inline markdown to simple HTML.

        This is a lightweight converter. For production use, a proper
        markdown library (e.g., markdown, mistune, or markdown-it)
        would be used.
        """
        if not markdown:
            return ""

        html = markdown

        # Escape HTML entities
        html = html.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")

        # Headings
        html = re.sub(
            r"^### (.+)$",
            r"<h3>\1</h3>",
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(
            r"^## (.+)$",
            r"<h2>\1</h2>",
            html,
            flags=re.MULTILINE,
        )
        html = re.sub(
            r"^# (.+)$",
            r"<h1>\1</h1>",
            html,
            flags=re.MULTILINE,
        )

        # Bold
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        # Italic
        html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)
        # Code inline
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

        # Links
        html = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">'
            f"{m.group(1)}</a>",
            html,
        )

        # Horizontal rules
        html = re.sub(r"^---+\s*$", "<hr>", html, flags=re.MULTILINE)

        # Paragraphs: wrap non-empty lines that aren't already HTML
        lines = html.splitlines()
        result = []
        in_code_block = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                if in_code_block:
                    result.append("<pre><code>")
                else:
                    result.append("</code></pre>")
                continue

            if in_code_block:
                result.append(stripped)
                continue

            if not stripped:
                result.append("")
                continue

            if stripped.startswith(("<h", "<hr", "<pre", "<table")):
                result.append(stripped)
                continue

            result.append(f"<p>{stripped}</p>")

        html = "\n".join(result)

        # Tables: simple pipe-table to HTML
        html = self._tables_to_html(html)

        return html

    def _tables_to_html(self, html: str) -> str:
        """Convert pipe tables to HTML tables."""
        lines = html.splitlines()
        result = []
        in_table = False
        table_lines: list[str] = []
        in_code = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("<pre>"):
                in_code = True
                result.append(line)
                continue
            if stripped.startswith("</pre>"):
                in_code = False
                result.append(line)
                continue
            if in_code:
                result.append(line)
                continue

            # Detect table row: starts and ends with |
            is_table_row = stripped.startswith("|") and stripped.endswith("|")

            if is_table_row:
                table_lines.append(stripped)
                in_table = True
            else:
                if in_table:
                    result.append(self._build_table_html(table_lines))
                    table_lines = []
                    in_table = False
                result.append(line)

        # Flush remaining table
        if in_table and table_lines:
            result.append(self._build_table_html(table_lines))

        return "\n".join(result)

    def _build_table_html(self, table_lines: list[str]) -> str:
        """Convert pipe-table lines to an HTML table."""
        if len(table_lines) < 2:
            return "\n".join(table_lines)

        rows: list[list[str]] = []
        for line in table_lines:
            # Strip leading/trailing pipes, split by |
            cells = [
                cell.strip() for cell in line.strip("|").split("|")
            ]
            rows.append(cells)

        # Detect separator row (contains ---)
        header = rows[0]
        if len(rows) > 1 and all(
            re.match(r"^[\s:-]+$", c) for c in rows[1]
        ):
            rows = [header] + rows[2:]  # skip separator

        if not rows:
            return ""

        html_parts = ['<table class="hermes-table">']
        # Header row
        html_parts.append("<thead><tr>")
        for cell in header:
            html_parts.append(f"<th>{cell}</th>")
        html_parts.append("</tr></thead>")

        # Data rows
        if len(rows) > 1:
            html_parts.append("<tbody>")
            for row in rows[1:]:
                html_parts.append("<tr>")
                for cell in row:
                    html_parts.append(f"<td>{cell}</td>")
                html_parts.append("</tr>")
            html_parts.append("</tbody>")

        html_parts.append("</table>")
        return "\n".join(html_parts)

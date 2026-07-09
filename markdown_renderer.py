"""Markdown rendering and enhancement for the Company dashboard."""

from __future__ import annotations

import re
from typing import Any


class MarkdownRenderer:
    """Renders markdown with automatic presentation enhancements."""

    _METRIC_RE = re.compile(
        r"^\s*([\w\s]+?)\s*:\s*"
        r"([\$€£]?\s*[\d,]+(?:\.\d+)?[%x]?\s*(?:[KMBkmb])?"
        r"|[A-Z]+\$\s*[\d,]+(?:\.\d+)?[MB]?)"
        r"\s*$"
    )

    _STATUSES = {
        "active", "blocked", "delayed", "done", "critical",
        "warning", "success", "failed", "pending", "in progress",
        "complete", "cancelled", "on hold", "approved", "rejected",
        "cold", "warm", "hot", "won", "lost", "blacklisted",
    }

    _CALLOUTS = {
        "note", "warning", "important", "todo",
        "info", "tip", "caution", "danger",
    }

    def render(self, markdown: str, tab_id: str) -> dict:
        sections = self._split_sections(markdown)
        metrics = self._extract_metrics(markdown)
        headings = self.extract_headings(markdown)
        raw_html = self._to_html(markdown)
        enhanced_sections = [self._enhance_section(s) for s in sections]
        return {
            "sections": enhanced_sections,
            "metrics": metrics,
            "headings": headings,
            "raw_html": raw_html,
            "word_count": len(markdown.split()),
        }

    def extract_headings(self, markdown: str) -> list[dict]:
        headings = []
        for line in markdown.splitlines():
            match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                anchor = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
                anchor = re.sub(r"[\s]+", "-", anchor)
                headings.append({"level": level, "text": text, "anchor": anchor})
        return headings

    def _split_sections(self, markdown: str) -> list[dict]:
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
                current = {"heading": text, "level": level, "anchor": anchor, "body": []}
            else:
                current["body"].append(line)
        if current["heading"] or current["body"]:
            current["body"] = "\n".join(current["body"]).strip()
            sections.append(current)
        return sections

    def _enhance_section(self, section: dict) -> dict:
        body = section.get("body", "")
        return {
            "heading": section.get("heading"),
            "level": section.get("level", 0),
            "anchor": section.get("anchor"),
            "type": self._detect_section_type(body),
            "body_html": self._to_html(body),
            "elements": self._parse_elements(body),
        }

    def _detect_section_type(self, body: str) -> str:
        lines = [l.strip() for l in body.splitlines() if l.strip()]
        if not lines:
            return "empty"
        if any(l.startswith("|") and l.endswith("|") for l in lines):
            if sum(1 for l in lines if l.startswith("|")) >= 2:
                return "table"
        metric_lines = sum(1 for l in lines if self._METRIC_RE.match(l))
        if lines and metric_lines / len(lines) > 0.4:
            return "metrics"
        if any(l.startswith(("- ", "* ", "+ ", "1. ")) for l in lines):
            list_lines = sum(1 for l in lines if re.match(r"^[\s]*[-*+\d\.]+\s", l))
            if lines and list_lines / len(lines) > 0.5:
                return "list"
        return "markdown"

    def _parse_elements(self, body: str) -> list[dict]:
        elements: list[dict] = []
        lines = body.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            lower = line.lower().strip(":*")
            if lower in self._STATUSES and len(line) < 30:
                elements.append({"type": "status", "text": line.strip("*:").strip(), "value": lower})
                i += 1
                continue
            if lower in self._CALLOUTS and line.endswith(":"):
                callout_lines = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    callout_lines.append(lines[i].strip())
                    i += 1
                elements.append({"type": "callout", "variant": lower, "text": " ".join(callout_lines)})
                continue
            metric_match = self._METRIC_RE.match(line)
            if metric_match:
                elements.append({"type": "metric", "label": metric_match.group(1).strip(), "value": metric_match.group(2).strip()})
                i += 1
                continue
            list_match = re.match(r"^[\s]*[-*+\d\.]+\s+(.+)$", line)
            if list_match:
                items = []
                while i < len(lines):
                    item_match = re.match(r"^[\s]*[-*+\d\.]+\s+(.+)$", lines[i].strip())
                    if item_match:
                        items.append({"text": item_match.group(1), "html": self._to_html(item_match.group(1))})
                        i += 1
                    else:
                        break
                elements.append({"type": "list_items", "items": items})
                continue
            elements.append({"type": "text", "text": line, "html": self._to_html(line)})
            i += 1
        return elements

    def _extract_metrics(self, markdown: str) -> list[dict]:
        metrics = []
        for line in markdown.splitlines():
            match = self._METRIC_RE.match(line.strip())
            if match:
                metrics.append({"label": match.group(1).strip(), "value": match.group(2).strip()})
        return metrics

    def _to_html(self, markdown: str) -> str:
        if not markdown:
            return ""
        html = markdown
        html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>',
            html,
        )
        html = re.sub(r"^---+\s*$", "<hr>", html, flags=re.MULTILINE)
        lines = html.splitlines()
        result = []
        in_code = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                result.append("<pre><code>" if in_code else "</code></pre>")
                continue
            if in_code:
                result.append(stripped)
                continue
            if not stripped or stripped.startswith(("<h", "<hr", "<pre", "<table")):
                result.append(stripped if stripped else "")
                continue
            result.append(f"<p>{stripped}</p>")
        html = "\n".join(result)
        html = self._tables_to_html(html)
        return html

    def _tables_to_html(self, html: str) -> str:
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
        if in_table and table_lines:
            result.append(self._build_table_html(table_lines))
        return "\n".join(result)

    def _build_table_html(self, table_lines: list[str]) -> str:
        if len(table_lines) < 2:
            return "\n".join(table_lines)
        rows = [[cell.strip() for cell in line.strip("|").split("|")] for line in table_lines]
        if len(rows) > 1 and all(re.match(r"^[\s:-]+$", c) for c in rows[1]):
            rows = [rows[0]] + rows[2:]
        if not rows:
            return ""
        parts = ['<table class="hermes-table">']
        parts.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in rows[0]) + "</tr></thead>")
        if len(rows) > 1:
            parts.append("<tbody>")
            for row in rows[1:]:
                parts.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
            parts.append("</tbody>")
        parts.append("</table>")
        return "\n".join(parts)
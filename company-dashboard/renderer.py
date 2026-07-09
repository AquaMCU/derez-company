"""ReportView component — renders a single report tab content.

Displays the enhanced report with metrics cards, status badges,
callout alerts, tables, table of contents, and auto-linking.
"""


class ReportView:
    """Renders a single report into Hermes dashboard UI primitives.

    Takes the enhanced report dict from the API and produces
    a renderable structure for the dashboard frontend.
    """

    @staticmethod
    def render(report_data: dict) -> dict:
        """Transform API report data into dashboard renderable structure.

        Args:
            report_data: The dict returned by the report API endpoint.

        Returns:
            A dict with Hermes UI primitives (panels, cards, sections...).
        """
        output = {
            "type": "report",
            "tab_id": report_data.get("tab_id", ""),
            "name": report_data.get("name", ""),
            "meta": {
                "word_count": report_data.get("content", {}).get(
                    "word_count", 0
                ),
            },
            "children": [],
        }

        content = report_data.get("content", {})
        sections = content.get("sections", [])
        metrics = content.get("metrics", [])
        headings = content.get("headings", [])
        raw_html = content.get("raw_html", "")

        # 1. Overview metric cards (if any)
        if metrics:
            output["children"].append(
                ReportView._render_metrics_row(metrics)
            )

        # 2. Table of contents panel (if multiple headings)
        if len(headings) > 1:
            output["children"].append(
                ReportView._render_toc(headings)
            )

        # 3. Enhanced sections
        for section in sections:
            output["children"].append(
                ReportView._render_section(section)
            )

        # 4. Fallback: raw HTML if no structured sections
        if not sections and raw_html:
            output["children"].append({
                "type": "panel",
                "children": [{"type": "html", "content": raw_html}],
            })

        return output

    @staticmethod
    def _render_metrics_row(metrics: list[dict]) -> dict:
        """Render a row of metric cards."""
        return {
            "type": "metrics_row",
            "metrics": [
                {
                    "type": "metric_card",
                    "label": m["label"],
                    "value": m["value"],
                }
                for m in metrics
            ],
        }

    @staticmethod
    def _render_toc(headings: list[dict]) -> dict:
        """Render a floating table of contents."""
        return {
            "type": "toc",
            "title": "On this page",
            "items": [
                {
                    "level": h["level"],
                    "text": h["text"],
                    "anchor": h["anchor"],
                }
                for h in headings
            ],
        }

    @staticmethod
    def _render_section(section: dict) -> dict:
        """Render a single enhanced section."""
        elements = section.get("elements", [])
        section_type = section.get("type", "markdown")
        heading = section.get("heading")

        children = []

        # Section heading
        if heading:
            children.append({
                "type": "section_heading",
                "level": section.get("level", 2),
                "text": heading,
                "anchor": section.get("anchor", ""),
            })

        # Map elements to Hermes UI primitives
        for elem in elements:
            elem_type = elem.get("type", "text")

            if elem_type == "metric":
                children.append({
                    "type": "metric_card",
                    "label": elem["label"],
                    "value": elem["value"],
                })

            elif elem_type == "status":
                children.append({
                    "type": "badge",
                    "text": elem["text"],
                    "variant": elem.get("value", "default"),
                })

            elif elem_type == "callout":
                children.append({
                    "type": "callout",
                    "variant": elem.get("variant", "note"),
                    "children": [
                        {"type": "text", "content": elem.get("text", "")}
                    ],
                })

            elif elem_type == "list_items":
                children.append({
                    "type": "card_group" if len(elem.get("items", [])) > 5
                    else "list",
                    "items": [
                        {
                            "type": "list_item",
                            "content": item.get("html", item.get("text", "")),
                        }
                        for item in elem.get("items", [])
                    ],
                })

            elif elem_type == "text":
                children.append({
                    "type": "text_block",
                    "content": elem.get("html", elem.get("text", "")),
                })

        # If no enhanced elements but we have body_html, render directly
        if not children and section.get("body_html"):
            children.append({
                "type": "html",
                "content": section["body_html"],
            })

        if section_type == "table":
            return {
                "type": "data_table",
                "title": heading,
                "html": section.get("body_html", ""),
                "children": children or None,
            }

        return {
            "type": "section",
            "heading": heading,
            "anchor": section.get("anchor"),
            "children": children,
            "fallback_html": section.get("body_html"),
        }


class EmptyState:
    """Renders the empty state when no reports exist."""

    @staticmethod
    def render() -> dict:
        return {
            "type": "empty_state",
            "icon": "file-text",
            "title": "No company reports found",
            "description": "Add markdown files to:\n\ncompany/reports",
            "action": {
                "label": "Rescan",
                "route": "/api/plugins/company-dashboard/scan",
                "method": "POST",
            },
        }


class ErrorState:
    """Renders error state for a failed report load."""

    @staticmethod
    def render(message: str, retry: bool = False) -> dict:
        result: dict = {
            "type": "error_panel",
            "title": "Failed to load report",
            "message": message,
        }
        if retry:
            result["action"] = {
                "label": "Retry",
                "route": "/api/plugins/company-dashboard/scan",
                "method": "POST",
            }
        return result


class TOC:
    """Renders a floating table of contents sidebar.

    Consumed by the dashboard frontend to generate a sticky TOC.
    """

    @staticmethod
    def render(headings: list[dict]) -> dict:
        if not headings:
            return {"type": "toc", "title": "On this page", "items": []}

        return {
            "type": "toc",
            "title": "On this page",
            "items": [
                {
                    "level": h["level"],
                    "text": h["text"],
                    "anchor": h["anchor"],
                }
                for h in headings
            ],
        }
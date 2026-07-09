"""ReportView — renders a single report tab content into Hermes UI primitives."""


class ReportView:
    """Transforms API report data into dashboard renderable structure."""

    @staticmethod
    def render(report_data: dict) -> dict:
        output = {
            "type": "report",
            "tab_id": report_data.get("tab_id", ""),
            "name": report_data.get("name", ""),
            "meta": {"word_count": report_data.get("content", {}).get("word_count", 0)},
            "children": [],
        }
        content = report_data.get("content", {})
        sections = content.get("sections", [])
        metrics = content.get("metrics", [])
        headings = content.get("headings", [])
        raw_html = content.get("raw_html", "")

        if metrics:
            output["children"].append(ReportView._render_metrics_row(metrics))
        if len(headings) > 1:
            output["children"].append(ReportView._render_toc(headings))
        for section in sections:
            output["children"].append(ReportView._render_section(section))
        if not sections and raw_html:
            output["children"].append({"type": "panel", "children": [{"type": "html", "content": raw_html}]})
        return output

    @staticmethod
    def _render_metrics_row(metrics: list[dict]) -> dict:
        return {
            "type": "metrics_row",
            "metrics": [{"type": "metric_card", "label": m["label"], "value": m["value"]} for m in metrics],
        }

    @staticmethod
    def _render_toc(headings: list[dict]) -> dict:
        return {
            "type": "toc",
            "title": "On this page",
            "items": [{"level": h["level"], "text": h["text"], "anchor": h["anchor"]} for h in headings],
        }

    @staticmethod
    def _render_section(section: dict) -> dict:
        elements = section.get("elements", [])
        section_type = section.get("type", "markdown")
        heading = section.get("heading")
        children = []
        if heading:
            children.append({"type": "section_heading", "level": section.get("level", 2), "text": heading, "anchor": section.get("anchor", "")})
        for elem in elements:
            t = elem.get("type", "text")
            if t == "metric":
                children.append({"type": "metric_card", "label": elem["label"], "value": elem["value"]})
            elif t == "status":
                children.append({"type": "badge", "text": elem["text"], "variant": elem.get("value", "default")})
            elif t == "callout":
                children.append({"type": "callout", "variant": elem.get("variant", "note"), "children": [{"type": "text", "content": elem.get("text", "")}]})
            elif t == "list_items":
                children.append({
                    "type": "card_group" if len(elem.get("items", [])) > 5 else "list",
                    "items": [{"type": "list_item", "content": item.get("html", item.get("text", ""))} for item in elem.get("items", [])],
                })
            elif t == "text":
                children.append({"type": "text_block", "content": elem.get("html", elem.get("text", ""))})
        if not children and section.get("body_html"):
            children.append({"type": "html", "content": section["body_html"]})
        if section_type == "table":
            return {"type": "data_table", "title": heading, "html": section.get("body_html", ""), "children": children or None}
        return {"type": "section", "heading": heading, "anchor": section.get("anchor"), "children": children, "fallback_html": section.get("body_html")}


class EmptyState:
    @staticmethod
    def render() -> dict:
        return {
            "type": "empty_state",
            "icon": "file-text",
            "title": "No company reports found",
            "description": "Add markdown files to:\n\ncompany/reports",
            "action": {"label": "Rescan", "route": "/api/plugins/company-dashboard/scan", "method": "POST"},
        }


class ErrorState:
    @staticmethod
    def render(message: str, retry: bool = False) -> dict:
        result = {"type": "error_panel", "title": "Failed to load report", "message": message}
        if retry:
            result["action"] = {"label": "Retry", "route": "/api/plugins/company-dashboard/scan", "method": "POST"}
        return result
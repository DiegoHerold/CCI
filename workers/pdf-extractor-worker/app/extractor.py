from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any


WORKER_TYPE = "pdf-extractor-worker"
WORKER_VERSION = "1.0.0"
MAX_REGEX_TEXT_LENGTH = 200_000
MAX_REGEX_PATTERN_LENGTH = 512


@dataclass
class ExtractionContext:
    request: dict[str, Any]
    preview_json: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    raw_fields: list[dict[str, Any]] = field(default_factory=list)
    raw_objects: list[dict[str, Any]] = field(default_factory=list)


def extract_pdf(request: dict[str, Any]) -> dict[str, Any]:
    preview_json = _preview_json(request)
    context = ExtractionContext(request=request, preview_json=preview_json)
    rules = request.get("template", {}).get("extraction_rules", []) or []
    if not rules:
        context.errors.append({"code": "template_rules_missing", "message": "Template has no extraction rules"})
        return _output(context, status="failed")

    for rule in rules:
        try:
            _run_rule(context, rule)
        except Exception as exc:
            context.errors.append({"code": "extraction_failed", "message": str(exc)})

    status = "completed"
    if context.errors and not context.raw_fields and not context.raw_objects:
        status = "failed"
    elif context.errors or context.warnings:
        status = "completed_with_warnings"
    return _output(context, status=status)


def _run_rule(context: ExtractionContext, rule: dict[str, Any]) -> None:
    strategy = _get(rule, "strategy")
    if strategy == "find_near_label":
        _extract_find_near_label(context, rule)
    elif strategy == "fixed_bbox":
        _extract_fixed_bbox(context, rule)
    elif strategy == "regex_from_text":
        _extract_regex_from_text(context, rule)
    elif strategy == "pdf_area_table":
        _extract_pdf_area_table(context, rule)
    elif strategy == "pdf_column_by_x_position":
        _extract_pdf_column_by_x_position(context, rule)
    elif strategy == "hierarchical_lines":
        _extract_hierarchical_lines(context, rule)
    else:
        context.errors.append(
            {
                "code": "rule_strategy_not_supported",
                "message": f"PDF strategy not supported: {strategy}",
            }
        )


def _extract_find_near_label(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    label = str(config.get("label", "")).strip()
    if not label:
        _invalid_config(context, rule, "find_near_label requires label")
        return
    position = str(config.get("position", "right")).lower()
    max_distance = float(config.get("max_distance", 200))
    candidates = [item for item in _text_items(context.preview_json) if label.casefold() in item["text"].casefold()]
    if not candidates:
        _not_found(context, rule, "field_not_found")
        return
    label_item = candidates[0]
    value = _value_near_label(context.preview_json, label_item, label, position, max_distance)
    if value is None:
        _not_found(context, rule, "field_not_found")
        return
    raw_value, evidence_item, distance = value
    confidence = max(0.45, min(0.95, 0.95 - (distance / max(max_distance, 1)) * 0.35))
    _add_field(context, rule, raw_value, confidence, _pdf_evidence(context, rule, evidence_item, confidence))


def _extract_fixed_bbox(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    bbox = config.get("bbox")
    page_number = int(config.get("page_number", config.get("pageNumber", 1)))
    if not isinstance(bbox, dict):
        _invalid_config(context, rule, "fixed_bbox requires bbox")
        return
    items = [
        item for item in _text_items(context.preview_json)
        if item["page_number"] == page_number and _intersects(item["bbox"], bbox)
    ]
    if not items:
        _not_found(context, rule, "bbox_not_found")
        return
    items.sort(key=lambda item: (item["bbox"]["y0"], item["bbox"]["x0"]))
    raw_value = " ".join(item["text"] for item in items).strip()
    merged = _merge_bbox([item["bbox"] for item in items])
    evidence_item = {**items[0], "text": raw_value, "bbox": merged}
    _add_field(context, rule, raw_value, 0.9, _pdf_evidence(context, rule, evidence_item, 0.9))


def _extract_regex_from_text(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    pattern = str(config.get("pattern", ""))
    if not pattern or len(pattern) > MAX_REGEX_PATTERN_LENGTH:
        _invalid_config(context, rule, "regex_from_text requires a bounded pattern")
        return
    text = "\n".join(item["text"] for item in _text_items(context.preview_json))[:MAX_REGEX_TEXT_LENGTH]
    try:
        match = re.search(pattern, text, flags=re.IGNORECASE)
    except re.error as exc:
        _invalid_config(context, rule, f"invalid regex: {exc}")
        return
    if not match:
        _not_found(context, rule, "field_not_found")
        return
    raw_value = match.group(1) if match.groups() else match.group(0)
    evidence_item = _first_item_containing(context.preview_json, raw_value) or {"page_number": 1, "bbox": {}, "text": raw_value}
    _add_field(context, rule, raw_value, 0.82, _pdf_evidence(context, rule, evidence_item, 0.82))


def _extract_pdf_area_table(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    bbox = config.get("bbox")
    columns = config.get("columns", [])
    page_number = int(config.get("page_number", config.get("pageNumber", 1)))
    if not isinstance(bbox, dict) or not isinstance(columns, list) or not columns:
        _invalid_config(context, rule, "pdf_area_table requires bbox and columns")
        return
    rows = _rows_in_area(context.preview_json, page_number, bbox)
    items = []
    for row_index, row in enumerate(rows):
        values: dict[str, Any] = {}
        for column in columns:
            path = str(_get(column, "field_path", ""))
            key = _leaf_name(path)
            x0 = float(column.get("x0", -math.inf))
            x1 = float(column.get("x1", math.inf))
            tokens = [token for token in row if x0 <= _center_x(token["bbox"]) <= x1]
            if not tokens:
                continue
            raw_value = " ".join(token["text"] for token in sorted(tokens, key=lambda item: item["bbox"]["x0"])).strip()
            confidence = 0.86
            values[key] = {
                "raw_value": raw_value,
                "confidence": confidence,
                "status": "extracted",
                "evidence": _pdf_evidence(context, rule, {**tokens[0], "text": raw_value, "bbox": _merge_bbox([t["bbox"] for t in tokens])}, confidence),
            }
        if values:
            items.append({"index": len(items), "values": values})
    if not items:
        _not_found(context, rule, "table_not_found")
        return
    context.raw_objects.append({"field_path": _field_path(rule), "field_type": "array", "items": items})


def _extract_pdf_column_by_x_position(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    bbox = config.get("bbox", {"x0": config.get("x0", -math.inf), "y0": config.get("y0", -math.inf), "x1": config.get("x1", math.inf), "y1": config.get("y1", math.inf)})
    page_number = int(config.get("page_number", config.get("pageNumber", 1)))
    x0 = float(config.get("x0", bbox.get("x0", -math.inf)))
    x1 = float(config.get("x1", bbox.get("x1", math.inf)))
    rows = _rows_in_area(context.preview_json, page_number, bbox)
    extracted = []
    for row in rows:
        tokens = [token for token in row if x0 <= _center_x(token["bbox"]) <= x1]
        if tokens:
            text = " ".join(token["text"] for token in sorted(tokens, key=lambda item: item["bbox"]["x0"])).strip()
            extracted.append(text)
    if not extracted:
        _not_found(context, rule, "field_not_found")
        return
    _add_field(context, rule, extracted, 0.78, _pdf_evidence(context, rule, _text_items(context.preview_json)[0], 0.78))


def _extract_hierarchical_lines(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    page_number = int(config.get("page_number", config.get("pageNumber", 1)))
    code_pattern = str(config.get("account_code_pattern", r"^\s*(\d+(?:\.\d+)*)\s+(.+)$"))
    try:
        pattern = re.compile(code_pattern)
    except re.error as exc:
        _invalid_config(context, rule, f"invalid hierarchy regex: {exc}")
        return
    items = []
    for line in _line_items(context.preview_json):
        if line["page_number"] != page_number:
            continue
        match = pattern.match(line["text"])
        if not match:
            continue
        code = match.group(1)
        remainder = match.group(2).strip()
        parts = remainder.rsplit(" ", 1)
        description = parts[0] if len(parts) == 2 and _looks_number(parts[1]) else remainder
        saldo = parts[1] if len(parts) == 2 and _looks_number(parts[1]) else None
        values = {
            "codigo": {"raw_value": code, "confidence": 0.84, "status": "extracted", "evidence": _pdf_evidence(context, rule, line, 0.84)},
            "descricao": {"raw_value": description, "confidence": 0.78, "status": "extracted", "evidence": _pdf_evidence(context, rule, line, 0.78)},
            "nivel": {"raw_value": code.count(".") + 1, "confidence": 0.8, "status": "extracted", "evidence": _pdf_evidence(context, rule, line, 0.8)},
        }
        if saldo is not None:
            values["saldo_atual"] = {"raw_value": saldo, "confidence": 0.72, "status": "extracted", "evidence": _pdf_evidence(context, rule, line, 0.72)}
        items.append({"index": len(items), "values": values})
    if not items:
        _not_found(context, rule, "field_not_found")
        return
    context.raw_objects.append({"field_path": _field_path(rule), "field_type": "array", "items": items})


def _output(context: ExtractionContext, status: str) -> dict[str, Any]:
    request = context.request
    template = request.get("template", {})
    document = request.get("document", {})
    raw_output = {
        "extraction_job_id": request.get("extraction_job_id"),
        "status": status,
        "worker_type": WORKER_TYPE,
        "worker_version": WORKER_VERSION,
        "template_id": template.get("template_id"),
        "template_version_id": template.get("template_version_id"),
        "document_id": document.get("document_id"),
        "raw_extracted_objects": context.raw_objects,
        "raw_extracted_fields": context.raw_fields,
        "warnings": context.warnings,
        "errors": context.errors,
    }
    return {
        "extraction_job_id": request.get("extraction_job_id"),
        "status": status,
        "raw_output": raw_output,
        "warnings": context.warnings,
        "errors": [error["code"] for error in context.errors],
    }


def _add_field(context: ExtractionContext, rule: dict[str, Any], raw_value: Any, confidence: float, evidence: dict[str, Any]) -> None:
    context.raw_fields.append(
        {
            "field_id": _get(rule, "field_id"),
            "field_path": _field_path(rule),
            "raw_value": raw_value,
            "data_type": _get(rule, "data_type", _get(rule, "field_type", "text")),
            "confidence": round(confidence, 4),
            "status": "extracted" if raw_value not in ("", None, []) else "not_found",
            "evidence": evidence,
        }
    )
    if confidence < 0.6:
        context.warnings.append(f"low_confidence:{_field_path(rule)}")


def _not_found(context: ExtractionContext, rule: dict[str, Any], warning: str) -> None:
    context.warnings.append(f"{warning}:{_field_path(rule)}")
    context.raw_fields.append(
        {
            "field_id": _get(rule, "field_id"),
            "field_path": _field_path(rule),
            "raw_value": None,
            "data_type": _get(rule, "data_type", _get(rule, "field_type", "text")),
            "confidence": 0.0,
            "status": "not_found",
            "evidence": None,
        }
    )


def _invalid_config(context: ExtractionContext, rule: dict[str, Any], message: str) -> None:
    context.errors.append({"code": "invalid_rule_config", "message": f"{_field_path(rule)}: {message}"})


def _pdf_evidence(context: ExtractionContext, rule: dict[str, Any], item: dict[str, Any], confidence: float) -> dict[str, Any]:
    return {
        "evidence_type": "pdf",
        "document_id": context.request.get("document", {}).get("document_id"),
        "page_number": item.get("page_number"),
        "bbox": item.get("bbox"),
        "source_text": item.get("text"),
        "rule_id": _get(rule, "id", _get(rule, "rule_id")),
        "rule_strategy": _get(rule, "strategy"),
        "confidence": round(confidence, 4),
    }


def _preview_json(request: dict[str, Any]) -> dict[str, Any]:
    preview = request.get("preview", {})
    return preview.get("preview_json") or preview.get("preview") or {}


def _field_path(rule: dict[str, Any]) -> str:
    return str(_get(rule, "field_path", _get(rule, "fieldPath", _get(rule, "path", ""))))


def _get(mapping: dict[str, Any], snake: str, default: Any = None) -> Any:
    if snake in mapping:
        return mapping[snake]
    parts = snake.split("_")
    camel = parts[0] + "".join(part.capitalize() for part in parts[1:])
    return mapping.get(camel, default)


def _text_items(preview: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    for page in preview.get("pages", []):
        page_number = int(page.get("page_number") or page.get("pageNumber") or 1)
        for line in page.get("lines", []):
            if line.get("tokens"):
                for token in line.get("tokens", []):
                    items.append({"page_number": page_number, "text": str(token.get("text", "")), "bbox": token.get("bbox") or line.get("bbox") or {}})
            elif line.get("text"):
                items.append({"page_number": page_number, "text": str(line.get("text", "")), "bbox": line.get("bbox") or {}})
        for block in page.get("text_blocks", []):
            items.append({"page_number": page_number, "text": str(block.get("text", "")), "bbox": block.get("bbox") or {}})
    return [item for item in items if item["text"]]


def _line_items(preview: dict[str, Any]) -> list[dict[str, Any]]:
    lines = []
    for page in preview.get("pages", []):
        page_number = int(page.get("page_number") or page.get("pageNumber") or 1)
        for line in page.get("lines", []):
            if line.get("text"):
                lines.append({"page_number": page_number, "text": str(line.get("text", "")), "bbox": line.get("bbox") or {}, "tokens": line.get("tokens", [])})
    return lines


def _value_near_label(preview: dict[str, Any], label_item: dict[str, Any], label: str, position: str, max_distance: float) -> tuple[str, dict[str, Any], float] | None:
    text = label_item["text"]
    label_index = text.casefold().find(label.casefold())
    remainder = text[label_index + len(label):].strip(" :;-") if label_index >= 0 else ""
    if remainder and position in {"right", "near"}:
        return remainder, {**label_item, "text": remainder}, 0.0
    candidates = []
    for item in _text_items(preview):
        if item is label_item or item["text"] == label_item["text"]:
            continue
        if item["page_number"] != label_item["page_number"]:
            continue
        if not _position_matches(label_item["bbox"], item["bbox"], position):
            continue
        distance = _bbox_distance(label_item["bbox"], item["bbox"])
        if distance <= max_distance:
            same_axis = _same_axis(label_item["bbox"], item["bbox"], position)
            candidates.append((0 if same_axis else 1, distance, item))
    if not candidates:
        return None
    _, distance, item = sorted(candidates, key=lambda pair: (pair[0], pair[1]))[0]
    return item["text"], item, distance


def _first_item_containing(preview: dict[str, Any], value: str) -> dict[str, Any] | None:
    value_cf = str(value).casefold()
    for item in _text_items(preview):
        if value_cf in item["text"].casefold():
            return item
    return None


def _rows_in_area(preview: dict[str, Any], page_number: int, bbox: dict[str, Any]) -> list[list[dict[str, Any]]]:
    tokens = [item for item in _text_items(preview) if item["page_number"] == page_number and _intersects(item["bbox"], bbox)]
    tokens.sort(key=lambda item: (item["bbox"].get("y0", 0), item["bbox"].get("x0", 0)))
    rows: list[list[dict[str, Any]]] = []
    for token in tokens:
        y = token["bbox"].get("y0", 0)
        for row in rows:
            if abs(row[0]["bbox"].get("y0", 0) - y) <= 4:
                row.append(token)
                break
        else:
            rows.append([token])
    return [sorted(row, key=lambda item: item["bbox"].get("x0", 0)) for row in rows]


def _position_matches(label_bbox: dict[str, Any], item_bbox: dict[str, Any], position: str) -> bool:
    if position == "right":
        return item_bbox.get("x0", 0) >= label_bbox.get("x1", 0)
    if position == "left":
        return item_bbox.get("x1", 0) <= label_bbox.get("x0", 0)
    if position == "below":
        return item_bbox.get("y0", 0) >= label_bbox.get("y1", 0)
    if position == "above":
        return item_bbox.get("y1", 0) <= label_bbox.get("y0", 0)
    return True


def _same_axis(label_bbox: dict[str, Any], item_bbox: dict[str, Any], position: str) -> bool:
    if position in {"right", "left"}:
        return not (item_bbox.get("y1", 0) < label_bbox.get("y0", 0) or item_bbox.get("y0", 0) > label_bbox.get("y1", 0))
    if position in {"above", "below"}:
        return not (item_bbox.get("x1", 0) < label_bbox.get("x0", 0) or item_bbox.get("x0", 0) > label_bbox.get("x1", 0))
    return True


def _bbox_distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax = (a.get("x0", 0) + a.get("x1", 0)) / 2
    ay = (a.get("y0", 0) + a.get("y1", 0)) / 2
    bx = (b.get("x0", 0) + b.get("x1", 0)) / 2
    by = (b.get("y0", 0) + b.get("y1", 0)) / 2
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _intersects(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return not (
        a.get("x1", 0) < b.get("x0", 0)
        or a.get("x0", 0) > b.get("x1", 0)
        or a.get("y1", 0) < b.get("y0", 0)
        or a.get("y0", 0) > b.get("y1", 0)
    )


def _merge_bbox(boxes: list[dict[str, Any]]) -> dict[str, float]:
    return {
        "x0": min(float(box.get("x0", 0)) for box in boxes),
        "y0": min(float(box.get("y0", 0)) for box in boxes),
        "x1": max(float(box.get("x1", 0)) for box in boxes),
        "y1": max(float(box.get("y1", 0)) for box in boxes),
    }


def _center_x(bbox: dict[str, Any]) -> float:
    return (float(bbox.get("x0", 0)) + float(bbox.get("x1", 0))) / 2


def _leaf_name(path: str) -> str:
    return path.replace("[]", "").split(".")[-1]


def _looks_number(value: str) -> bool:
    return bool(re.search(r"\d", value)) and bool(re.match(r"^[\d.,()\-]+$", value.strip()))

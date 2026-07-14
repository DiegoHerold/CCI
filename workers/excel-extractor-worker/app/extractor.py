from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


WORKER_TYPE = "excel-extractor-worker"
WORKER_VERSION = "1.0.0"


@dataclass
class ExtractionContext:
    request: dict[str, Any]
    preview_json: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    raw_fields: list[dict[str, Any]] = field(default_factory=list)
    raw_objects: list[dict[str, Any]] = field(default_factory=list)


def extract_excel(request: dict[str, Any]) -> dict[str, Any]:
    preview_json = _preview_json(request)
    context = ExtractionContext(request=request, preview_json=preview_json)
    rules = request.get("template", {}).get("extraction_rules", []) or []
    if not rules:
        context.errors.append({"code": "template_rules_missing", "message": "Template has no extraction rules"})
        return _output(context, "failed")

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
    return _output(context, status)


def _run_rule(context: ExtractionContext, rule: dict[str, Any]) -> None:
    strategy = _get(rule, "strategy")
    if strategy == "excel_cell_address":
        _extract_cell_address(context, rule)
    elif strategy == "excel_column_by_header":
        _extract_column_by_header(context, rule)
    elif strategy == "excel_range_table":
        _extract_range_table(context, rule)
    elif strategy == "excel_sheet_by_name":
        _extract_sheet_by_name(context, rule)
    elif strategy in {"excel_named_range", "excel_header_row_detection", "excel_hierarchical_rows"}:
        context.errors.append({"code": "rule_strategy_not_supported", "message": f"Excel strategy prepared but not enabled yet: {strategy}"})
    else:
        context.errors.append({"code": "rule_strategy_not_supported", "message": f"Excel strategy not supported: {strategy}"})


def _extract_cell_address(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    sheet = _find_sheet(context.preview_json, config)
    if sheet is None:
        _error(context, "sheet_not_found", rule, "sheet not found")
        return
    address = str(config.get("cell") or config.get("address") or "").upper()
    if not address:
        _invalid_config(context, rule, "excel_cell_address requires cell")
        return
    cell = _cell_map(sheet).get(address)
    if cell is None:
        _not_found(context, rule, "cell_not_found")
        return
    raw_value = _cell_value(cell)
    confidence = 0.95 if raw_value not in ("", None) else 0.0
    if confidence == 0.0:
        _not_found(context, rule, "field_not_found")
        return
    _add_field(context, rule, raw_value, confidence, _excel_evidence(context, rule, sheet, cell, confidence))


def _extract_column_by_header(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    sheet = _find_sheet(context.preview_json, config)
    if sheet is None:
        _error(context, "sheet_not_found", rule, "sheet not found")
        return
    column = _resolve_column(sheet, config, context, rule)
    if column is None:
        _not_found(context, rule, "header_not_found")
        return
    start_row = int(config.get("start_row") or config.get("startRow") or 2)
    values = []
    for cell in sorted(sheet.get("cells", []), key=lambda item: int(item.get("row", 0))):
        if int(cell.get("row", 0)) < start_row or int(cell.get("column", 0)) != column:
            continue
        raw_value = _cell_value(cell)
        if raw_value in ("", None):
            continue
        confidence = 0.9
        values.append(
            {
                "raw_value": raw_value,
                "confidence": confidence,
                "status": "extracted",
                "evidence": _excel_evidence(context, rule, sheet, cell, confidence),
            }
        )
    if not values:
        _not_found(context, rule, "field_not_found")
        return
    _add_field(context, rule, values, 0.88, values[0]["evidence"])


def _extract_range_table(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    sheet = _find_sheet(context.preview_json, config)
    if sheet is None:
        _error(context, "sheet_not_found", rule, "sheet not found")
        return
    table_range = str(config.get("range") or _first_detected_table_range(sheet) or "")
    bounds = _parse_range(table_range, sheet)
    if bounds is None:
        _invalid_config(context, rule, "excel_range_table requires a valid range")
        return
    min_row, min_col, max_row, max_col = bounds
    columns = config.get("columns", [])
    if not isinstance(columns, list) or not columns:
        _invalid_config(context, rule, "excel_range_table requires columns")
        return
    header_row = int(config.get("header_row") or config.get("headerRow") or min_row)
    start_row = int(config.get("start_row") or config.get("startRow") or header_row + 1)
    cell_map = _cell_map(sheet)
    header_by_name = _headers_by_name(sheet, header_row, min_col, max_col)
    column_specs: list[tuple[str, int]] = []
    for column in columns:
        path = str(_get(column, "field_path", ""))
        key = _leaf_name(path)
        col_index = None
        if column.get("column") is not None:
            col_index = int(column["column"])
        elif column.get("column_letter") or column.get("columnLetter"):
            col_index = _column_index(str(column.get("column_letter") or column.get("columnLetter")))
        elif column.get("header"):
            col_index = header_by_name.get(_normalize_text(str(column.get("header"))))
        if col_index is None:
            context.warnings.append(f"header_not_found:{key}")
            continue
        column_specs.append((key, col_index))
    if not column_specs:
        _not_found(context, rule, "header_not_found")
        return

    items = []
    for row in range(start_row, max_row + 1):
        values: dict[str, Any] = {}
        for key, col_index in column_specs:
            if col_index < min_col or col_index > max_col:
                continue
            address = f"{_column_letter(col_index)}{row}"
            cell = cell_map.get(address)
            raw_value = _cell_value(cell) if cell else None
            if raw_value in ("", None):
                continue
            confidence = 0.9
            values[key] = {
                "raw_value": raw_value,
                "confidence": confidence,
                "status": "extracted",
                "evidence": _excel_evidence(context, rule, sheet, cell, confidence),
            }
        if not values:
            context.warnings.append(f"empty_row_ignored:{row}")
            continue
        _apply_hierarchy(values, config)
        items.append({"index": len(items), "values": values})
    if not items:
        _not_found(context, rule, "table_not_found")
        return
    context.raw_objects.append({"field_path": _field_path(rule), "field_type": "array", "items": items})


def _extract_sheet_by_name(context: ExtractionContext, rule: dict[str, Any]) -> None:
    config = _get(rule, "config", {}) or {}
    sheet = _find_sheet(context.preview_json, config)
    if sheet is None:
        _error(context, "sheet_not_found", rule, "sheet not found")
        return
    confidence = 0.92
    evidence = {
        "evidence_type": "excel",
        "document_id": context.request.get("document", {}).get("document_id"),
        "sheet_name": sheet.get("name"),
        "cell_range": None,
        "source_value": sheet.get("name"),
        "rule_id": _get(rule, "id", _get(rule, "rule_id")),
        "rule_strategy": _get(rule, "strategy"),
        "confidence": confidence,
    }
    _add_field(context, rule, sheet.get("name"), confidence, evidence)


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


def _add_field(context: ExtractionContext, rule: dict[str, Any], raw_value: Any, confidence: float, evidence: dict[str, Any] | None) -> None:
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


def _error(context: ExtractionContext, code: str, rule: dict[str, Any], message: str) -> None:
    context.errors.append({"code": code, "message": f"{_field_path(rule)}: {message}"})


def _invalid_config(context: ExtractionContext, rule: dict[str, Any], message: str) -> None:
    _error(context, "invalid_rule_config", rule, message)


def _excel_evidence(context: ExtractionContext, rule: dict[str, Any], sheet: dict[str, Any], cell: dict[str, Any] | None, confidence: float) -> dict[str, Any]:
    address = cell.get("address") if cell else None
    return {
        "evidence_type": "excel",
        "document_id": context.request.get("document", {}).get("document_id"),
        "sheet_name": sheet.get("name"),
        "cell_range": f"{address}:{address}" if address else None,
        "source_value": _cell_value(cell) if cell else None,
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


def _find_sheet(preview: dict[str, Any], config: dict[str, Any]) -> dict[str, Any] | None:
    sheets = preview.get("sheets", [])
    if not sheets:
        return None
    aliases = []
    for key in ("sheet_name", "sheetName", "sheet_aliases", "sheetAliases"):
        value = config.get(key)
        if isinstance(value, list):
            aliases.extend(str(item) for item in value)
        elif value:
            aliases.append(str(value))
    if not aliases:
        return sheets[0]
    normalized = {_normalize_text(alias) for alias in aliases}
    for sheet in sheets:
        if _normalize_text(str(sheet.get("name", ""))) in normalized:
            return sheet
    return None


def _cell_map(sheet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(cell.get("address", "")).upper(): cell for cell in sheet.get("cells", [])}


def _cell_value(cell: dict[str, Any] | None) -> Any:
    if cell is None:
        return None
    value = cell.get("value")
    return cell.get("raw_value") if value is None else value


def _resolve_column(sheet: dict[str, Any], config: dict[str, Any], context: ExtractionContext, rule: dict[str, Any]) -> int | None:
    if config.get("column") is not None:
        return int(config["column"])
    if config.get("column_letter") or config.get("columnLetter"):
        return _column_index(str(config.get("column_letter") or config.get("columnLetter")))
    aliases = config.get("header_aliases") or config.get("headerAliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    normalized_aliases = {_normalize_text(str(alias)) for alias in aliases}
    matches = []
    header_rows = sheet.get("detected_headers", []) or [{"row": 1}]
    for header in header_rows:
        row = int(header.get("row", 1))
        for cell in sheet.get("cells", []):
            if int(cell.get("row", 0)) == row and _normalize_text(str(_cell_value(cell))) in normalized_aliases:
                matches.append(int(cell.get("column", 0)))
    if len(matches) > 1:
        context.warnings.append(f"ambiguous_header:{_field_path(rule)}")
    return matches[0] if matches else None


def _headers_by_name(sheet: dict[str, Any], row: int, min_col: int, max_col: int) -> dict[str, int]:
    headers = {}
    for cell in sheet.get("cells", []):
        col = int(cell.get("column", 0))
        if int(cell.get("row", 0)) == row and min_col <= col <= max_col:
            value = _cell_value(cell)
            if value not in ("", None):
                headers[_normalize_text(str(value))] = col
    return headers


def _first_detected_table_range(sheet: dict[str, Any]) -> str | None:
    tables = sheet.get("detected_tables") or sheet.get("detectedTables") or []
    return tables[0].get("range") if tables else None


def _parse_range(value: str, sheet: dict[str, Any]) -> tuple[int, int, int, int] | None:
    if not value:
        max_row = int(sheet.get("max_row") or sheet.get("maxRow") or 0)
        max_col = int(sheet.get("max_column") or sheet.get("maxColumn") or 0)
        return (1, 1, max_row, max_col) if max_row and max_col else None
    match = re.match(r"^([A-Z]+)(\d+):([A-Z]+)(\d+)$", value.upper())
    if not match:
        return None
    c1, r1, c2, r2 = match.groups()
    return int(r1), _column_index(c1), int(r2), _column_index(c2)


def _column_index(letters: str) -> int:
    total = 0
    for char in letters.upper():
        if not ("A" <= char <= "Z"):
            continue
        total = total * 26 + (ord(char) - ord("A") + 1)
    return total


def _column_letter(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def _apply_hierarchy(values: dict[str, Any], config: dict[str, Any]) -> None:
    hierarchy = config.get("hierarchy") or {}
    if not hierarchy.get("enabled"):
        return
    code_field = _leaf_name(str(hierarchy.get("account_code_field") or hierarchy.get("accountCodeField") or "codigo"))
    code_value = values.get(code_field, {}).get("raw_value")
    if not code_value:
        return
    level = str(code_value).count(".") + 1
    values["nivel"] = {"raw_value": level, "confidence": 0.8, "status": "extracted", "evidence": values[code_field].get("evidence")}


def _leaf_name(path: str) -> str:
    return path.replace("[]", "").split(".")[-1]


def _normalize_text(value: str) -> str:
    without_accents = unicodedata.normalize("NFKD", value)
    return "".join(char for char in without_accents if not unicodedata.combining(char)).strip().casefold()

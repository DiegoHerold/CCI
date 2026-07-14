from __future__ import annotations

import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from typing import Any


CNPJ_RE = re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b")
DATE_RE = re.compile(r"\b(?:\d{2}/\d{2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b")
CURRENCY_RE = re.compile(r"(?:R\$\s*)?-?\d{1,3}(?:\.\d{3})*,\d{2}\b")
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9_]{3,}")


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.lower()
    return re.sub(r"\s+", " ", text).strip()


def _first(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _preview_payload(response: dict[str, Any] | None) -> dict[str, Any]:
    if not response:
        return {}
    preview = response.get("preview")
    return preview if isinstance(preview, dict) else response


def _append_text(parts: list[str], value: Any, limit: int) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text and sum(len(part) for part in parts) < limit:
        parts.append(text)


def _keywords(normalized_text: str, limit: int) -> list[str]:
    counter = Counter(WORD_RE.findall(normalized_text))
    return [word for word, _ in counter.most_common(limit)]


def _regex_patterns(text: str) -> list[str]:
    patterns: list[str] = []
    if CNPJ_RE.search(text):
        patterns.append("cnpj")
    if DATE_RE.search(text):
        patterns.append("date")
    if CURRENCY_RE.search(text):
        patterns.append("currency")
    return patterns


def build_document_profile(
    document: dict[str, Any],
    preview_response: dict[str, Any],
    *,
    text_limit: int,
    keyword_limit: int,
) -> dict[str, Any]:
    preview = _preview_payload(preview_response)
    file_format = str(
        _first(document, "file_format", "fileFormat", "extension", default=_first(preview, "file_format", "fileFormat", default=""))
    ).upper().lstrip(".")
    parts: list[str] = []
    sheet_names: list[str] = []
    detected_headers: list[str] = []
    structure_hints: set[str] = set()
    page_count = 0
    sheet_count = 0
    table_count = 0
    requires_ocr = bool(_first(preview, "requires_ocr", "requiresOcr", default=False))

    if file_format == "PDF":
        pages = preview.get("pages") or []
        page_count = int(_first(preview.get("summary", {}) if isinstance(preview.get("summary"), dict) else {}, "page_count", "pageCount", default=len(pages)) or 0)
        for page in pages:
            for block in page.get("text_blocks", page.get("textBlocks", [])) or []:
                _append_text(parts, block.get("text"), text_limit)
            for line in page.get("lines", []) or []:
                _append_text(parts, line.get("text"), text_limit)
            tables = page.get("tables", []) or []
            table_count += len(tables)
        if page_count:
            structure_hints.add("text")
        if table_count:
            structure_hints.add("table")
            if page_count > 1:
                structure_hints.add("hierarchical")
        if requires_ocr:
            structure_hints.add("requires_ocr")
    elif file_format in {"XLS", "XLSX", "CSV"}:
        sheets = preview.get("sheets") or []
        sheet_count = int(_first(preview.get("summary", {}) if isinstance(preview.get("summary"), dict) else {}, "sheet_count", "sheetCount", default=len(sheets)) or 0)
        for sheet in sheets:
            name = str(sheet.get("name") or "")
            if name:
                sheet_names.append(name)
                _append_text(parts, name, text_limit)
            for header in sheet.get("detected_headers", sheet.get("detectedHeaders", [])) or []:
                values = header.get("values") if isinstance(header, dict) else None
                for value in values or []:
                    if value is not None:
                        detected_headers.append(str(value))
                        _append_text(parts, value, text_limit)
            for cell in sheet.get("cells", []) or []:
                _append_text(parts, cell.get("value", cell.get("raw_value")), text_limit)
            tables = sheet.get("detected_tables", sheet.get("detectedTables", [])) or []
            table_count += len(tables)
        if sheet_count:
            structure_hints.add("table")
        if table_count or len(sheet_names) > 1:
            structure_hints.add("mixed")

    summary = preview.get("summary") if isinstance(preview.get("summary"), dict) else {}
    table_count = max(table_count, int(_first(summary, "table_count", "tableCount", default=0) or 0))
    text_sample = "\n".join(parts)[:text_limit]
    normalized = normalize_text(text_sample)
    patterns = _regex_patterns(text_sample)

    return {
        "document_id": _first(document, "document_id", "documentId", default=_first(preview, "document_id", "documentId")),
        "client_id": _first(document, "client_id", "clientId"),
        "competence_id": _first(document, "competence_id", "competenceId"),
        "file_format": file_format,
        "mime_type": _first(document, "mime_type", "mimeType"),
        "original_filename": _first(document, "original_filename", "originalFilename", "filename"),
        "page_count": page_count,
        "sheet_count": sheet_count,
        "requires_ocr": requires_ocr,
        "text_sample": text_sample,
        "normalized_text_sample": normalized,
        "detected_keywords": _keywords(normalized, keyword_limit),
        "detected_regex_patterns": patterns,
        "has_cnpj": "cnpj" in patterns,
        "has_dates": "date" in patterns,
        "has_currency_values": "currency" in patterns,
        "has_tables": table_count > 0,
        "structure_hints": sorted(structure_hints),
        "sheet_names": sheet_names,
        "detected_headers": detected_headers,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

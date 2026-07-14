import re
from decimal import Decimal, InvalidOperation
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.application.schemas import (
    AnnotationResponse,
    AnnotationWithRuleCreate,
    AnnotationWithRuleResponse,
    ExtractionRuleCreate,
    ExtractionRuleResponse,
    ExtractionStrategy,
    FieldResponse,
    IdentificationSignalResponse,
    RulePreviewNormalizationRequest,
    RulePreviewNormalizationResponse,
    SuggestedArrayResponse,
    SuggestedFieldResponse,
    SuggestedRuleResponse,
    SuggestedTemplateResponse,
    TemplateBuilderStateResponse,
    TemplateSuggestionResponse,
    TemplateDetail,
    TemplateVersionResponse,
)
from app.application.services import TemplateService
from app.dependencies import get_document_service, get_template_service
from app.domain.enums import TemplateVersionStatus
from app.errors import NotFoundError
from app.infrastructure.document_service import DocumentServicePort


router = APIRouter(tags=["template-builder"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
DocumentServiceDep = Annotated[DocumentServicePort, Depends(get_document_service)]


def _field_path(service: TemplateService, template_id: str, field_id: str) -> str:
    for field in service.list_fields(template_id):
        if field.id == field_id:
            return field.field_path
    return field_id


def _suggest_rule(selection_type: str, payload: dict[str, Any], selected_text: str | None, field_path: str) -> tuple[ExtractionStrategy, dict[str, Any]]:
    if selection_type in {"pdf_text_block", "pdf_line", "pdf_token"}:
        if selected_text and ":" in selected_text:
            label = selected_text.split(":", 1)[0].strip()
            return ExtractionStrategy.FIND_NEAR_LABEL, {
                "field_path": field_path,
                "label": label,
                "position": "right",
                "max_distance": 200,
            }
        return ExtractionStrategy.FIXED_BBOX, {
            "field_path": field_path,
            "page_number": payload.get("page_number"),
            "bbox": payload.get("bbox"),
        }
    if selection_type == "pdf_area":
        return ExtractionStrategy.FIXED_BBOX, {
            "field_path": field_path,
            "page_number": payload.get("page_number"),
            "bbox": payload.get("bbox"),
        }
    if selection_type == "pdf_table_candidate":
        return ExtractionStrategy.PDF_AREA_TABLE, {
            "field_path": field_path,
            "page_number": payload.get("page_number"),
            "bbox": payload.get("bbox"),
            "columns": [],
        }
    if selection_type == "excel_cell":
        cell = payload.get("cell") if isinstance(payload.get("cell"), dict) else {}
        return ExtractionStrategy.EXCEL_CELL_ADDRESS, {
            "field_path": field_path,
            "sheet_name": payload.get("sheet_name"),
            "cell": cell.get("address") or payload.get("address"),
        }
    if selection_type == "excel_column":
        aliases = [item for item in [payload.get("header"), selected_text] if item]
        return ExtractionStrategy.EXCEL_COLUMN_BY_HEADER, {
            "field_path": field_path,
            "sheet_name": payload.get("sheet_name"),
            "header_aliases": aliases,
            "column_letter": payload.get("column_letter"),
        }
    if selection_type in {"excel_range", "excel_table_candidate"}:
        return ExtractionStrategy.EXCEL_RANGE_TABLE, {
            "field_path": field_path,
            "sheet_name": payload.get("sheet_name"),
            "range": payload.get("range"),
            "header_row": payload.get("header_row"),
            "start_row": payload.get("start_row"),
        }
    return ExtractionStrategy.FIND_NEAR_LABEL, {"field_path": field_path}


def _walk_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _text_items(preview: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _walk_dicts(preview):
        text = item.get("text") or item.get("value") or item.get("source_text") or item.get("source_value")
        if text is None:
            continue
        text_value = str(text).strip()
        if not text_value:
            continue
        items.append(
            {
                "text": text_value,
                "page_number": item.get("page_number") or item.get("page") or item.get("pageIndex"),
                "bbox": item.get("bbox"),
                "sheet_name": item.get("sheet_name") or item.get("sheetName") or item.get("sheet"),
                "cell_range": item.get("address") or item.get("cell") or item.get("range"),
            }
        )
    return items[:2000]


def _all_text(items: list[dict[str, Any]]) -> str:
    return "\n".join(str(item["text"]) for item in items)


def _detect_headers(items: list[dict[str, Any]]) -> set[str]:
    normalized = {_strip_accents(str(item["text"]).casefold()) for item in items}
    headers: set[str] = set()
    for value in normalized:
        if value in {"conta", "codigo", "codigo da conta", "classificacao"}:
            headers.add("conta")
        if value in {"descricao", "descrição", "historico", "histórico"}:
            headers.add("descricao")
        if "saldo" in value:
            headers.add("saldo")
        if "debito" in value or "débito" in value:
            headers.add("debito")
        if "credito" in value or "crédito" in value:
            headers.add("credito")
    return headers


def _document_file_format(document: dict[str, Any], preview: dict[str, Any]) -> str:
    return str(document.get("fileFormat") or document.get("file_format") or preview.get("file_format") or "PDF").upper()


def _evidence_from_item(item: dict[str, Any], field_path: str, strategy: str) -> dict[str, Any]:
    evidence = {
        "field_path": field_path,
        "rule_strategy": strategy,
        "source_text": item.get("text"),
    }
    if item.get("page_number") is not None:
        evidence.update({"evidence_type": "pdf", "page_number": item.get("page_number"), "bbox": item.get("bbox")})
    if item.get("sheet_name") or item.get("cell_range"):
        evidence.update({"evidence_type": "excel", "sheet_name": item.get("sheet_name"), "cell_range": item.get("cell_range")})
    return evidence


def _normalize_preview(raw_value: Any, field_type: str) -> tuple[Any, str | None, str]:
    if raw_value is None or raw_value == "":
        return None, None, "not_found"
    text = str(raw_value).strip()
    normalized_type = field_type.lower()
    if normalized_type == "cnpj":
        digits = re.sub(r"\D", "", text)
        if len(digits) < 14:
            return digits or None, text, "invalid"
        digits = digits[:14]
        return digits, f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}", "valid"
    if normalized_type in {"month", "competence"}:
        match = re.search(r"\b(\d{1,2})/(\d{4})\b", text)
        if match:
            month, year = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12:
                return f"{year:04d}-{month:02d}", f"{month:02d}/{year:04d}", "valid"
        match = re.search(r"\b(\d{4})-(\d{1,2})\b", text)
        if match:
            year, month = int(match.group(1)), int(match.group(2))
            if 1 <= month <= 12:
                return f"{year:04d}-{month:02d}", f"{month:02d}/{year:04d}", "valid"
        return None, text, "invalid"
    if normalized_type in {"money", "number", "percentage"}:
        parsed = _parse_decimal(text.replace("%", ""))
        if parsed is None:
            return None, text, "invalid"
        if normalized_type == "percentage" and "%" in text:
            parsed = parsed / Decimal("100")
        return str(parsed), str(parsed), "valid"
    if normalized_type == "account_code":
        compact = re.sub(r"\s+", "", text)
        return compact, compact, "valid" if re.match(r"^\d+(?:\.\d+)*$", compact) else "invalid"
    return re.sub(r"\s+", " ", text), re.sub(r"\s+", " ", text), "valid"


def _parse_decimal(value: str) -> Decimal | None:
    text = value.strip().upper()
    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = re.sub(r"\b[DC]\b$", "", text)
    text = text.replace("R$", "").replace("(", "").replace(")", "").replace("+", "").replace("-", "")
    text = re.sub(r"[^0-9,\.]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".") if text.rfind(",") > text.rfind(".") else text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return None
    return -parsed if negative else parsed


def _strip_accents(value: str) -> str:
    replacements = str.maketrans({"ç": "c", "ã": "a", "õ": "o", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "â": "a", "ê": "e", "ô": "o"})
    return value.translate(replacements)


def _find_value_for_rule(items: list[dict[str, Any]], field_type: str, rule: dict[str, Any]) -> tuple[Any, dict[str, Any], float]:
    strategy = str(rule.get("strategy") or rule.get("rule_strategy") or "")
    config = rule.get("config") if isinstance(rule.get("config"), dict) else rule
    label = str(config.get("label") or "").strip()
    regex = config.get("regex") or config.get("pattern")
    if regex:
        pattern = re.compile(str(regex), flags=re.IGNORECASE)
        for item in items:
            match = pattern.search(str(item["text"]))
            if match:
                return match.group(1) if match.groups() else match.group(0), _evidence_from_item(item, "", strategy), 0.88
    if label:
        label_folded = _strip_accents(label.casefold())
        for item in items:
            text = str(item["text"])
            folded = _strip_accents(text.casefold())
            if label_folded in folded:
                after = text.split(":", 1)[1].strip() if ":" in text else text
                return _best_raw_for_type(after, field_type), _evidence_from_item(item, "", strategy or "find_near_label"), 0.86
    if strategy == "excel_cell_address":
        wanted = str(config.get("cell") or config.get("address") or "").upper()
        for item in items:
            if str(item.get("cell_range") or "").upper() == wanted:
                return item["text"], _evidence_from_item(item, "", strategy), 0.9
    sample = _best_raw_for_type(_all_text(items), field_type)
    evidence_item = next((item for item in items if str(sample) in str(item["text"])), items[0] if items else {})
    return sample, _evidence_from_item(evidence_item, "", strategy or "regex_from_text"), 0.72 if sample else 0.0


def _best_raw_for_type(text: str, field_type: str) -> str | None:
    if field_type == "cnpj":
        match = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", text)
        return match.group(0) if match else None
    if field_type in {"month", "competence"}:
        match = re.search(r"\b(?:\d{1,2}/\d{4}|\d{4}-\d{1,2})\b", text)
        return match.group(0) if match else None
    if field_type in {"money", "number"}:
        match = re.search(r"(?:R\$\s*)?-?\(?\d{1,3}(?:\.\d{3})*,\d{2}\)?\s*[DC]?", text, flags=re.IGNORECASE)
        return match.group(0) if match else None
    if field_type == "account_code":
        match = re.search(r"\b\d+(?:\.\d+)+\b", text)
        return match.group(0) if match else None
    return text.strip()[:512] if text.strip() else None


@router.get("/templates/{template_id}/builder-state", response_model=TemplateBuilderStateResponse)
def get_builder_state(template_id: str, service: TemplateServiceDep) -> TemplateBuilderStateResponse:
    template = service.get_template(template_id)
    versions = service.list_versions(template_id)
    active_version = next((item for item in versions if item.id == template.active_version_id), None)
    draft_version = next((item for item in versions if item.status == TemplateVersionStatus.DRAFT.value), None)
    return TemplateBuilderStateResponse(
        template=TemplateDetail.from_entity(template),
        active_version=TemplateVersionResponse.from_entity(active_version) if active_version else None,
        draft_version=TemplateVersionResponse.from_entity(draft_version) if draft_version else None,
        fields=[FieldResponse.from_entity(item) for item in service.list_fields(template_id)],
        annotations=[AnnotationResponse.from_entity(item) for item in service.list_annotations(template_id, field_id=None, document_id=None, annotation_type=None)],
        extraction_rules=[ExtractionRuleResponse.from_entity(item) for item in service.list_rules(template_id)],
        identification_signals=[IdentificationSignalResponse.from_entity(item) for item in service.list_signals(template_id)],
    )


@router.post(
    "/templates/{template_id}/annotations/with-rule",
    response_model=AnnotationWithRuleResponse,
    status_code=201,
)
def create_annotation_with_rule(
    template_id: str,
    payload: AnnotationWithRuleCreate,
    service: TemplateServiceDep,
) -> AnnotationWithRuleResponse:
    annotation = service.create_annotation(template_id, payload)
    field_path = _field_path(service, template_id, payload.field_id)
    selection_type = payload.selection_payload.get("selection_type", payload.annotation_type.value)
    suggested_strategy, suggested_config = _suggest_rule(
        selection_type,
        payload.selection_payload,
        payload.selected_text,
        field_path,
    )
    rule = None
    if payload.generate_rule:
        rule = service.create_rule(
            template_id,
            ExtractionRuleCreate(
                template_version_id=None,
                field_id=payload.field_id,
                strategy=payload.rule_strategy or suggested_strategy,
                config=payload.rule_config or suggested_config,
                confidence_hint=payload.confidence_hint,
                created_from_annotation_id=annotation.id,
            ),
        )
    return AnnotationWithRuleResponse(
        annotation=AnnotationResponse.from_entity(annotation),
        extraction_rule=ExtractionRuleResponse.from_entity(rule) if rule else None,
        suggested_strategy=payload.rule_strategy or suggested_strategy,
        suggested_config=payload.rule_config or suggested_config,
    )


@router.post("/templates/from-document/{document_id}/suggestions", response_model=TemplateSuggestionResponse)
async def suggest_template_from_document(
    document_id: str,
    service: TemplateServiceDep,
    document_service: DocumentServiceDep,
) -> TemplateSuggestionResponse:
    document = await document_service.get_document(
        document_id,
        authorization=service.principal.authorization,
        correlation_id=service.correlation_id,
    )
    preview_response = await document_service.get_preview(
        document_id,
        authorization=service.principal.authorization,
        correlation_id=service.correlation_id,
    )
    if document is None or preview_response is None:
        raise NotFoundError("Document preview")
    preview = preview_response.get("preview") if isinstance(preview_response.get("preview"), dict) else preview_response
    items = _text_items(preview)
    text = _all_text(items)
    file_format = _document_file_format(document, preview)
    headers = _detect_headers(items)

    fields: list[SuggestedFieldResponse] = []
    arrays: list[SuggestedArrayResponse] = []
    rules: list[SuggestedRuleResponse] = []
    warnings: list[str] = []

    cnpj = _best_raw_for_type(text, "cnpj")
    if cnpj:
        normalized, display, status = _normalize_preview(cnpj, "cnpj")
        fields.append(SuggestedFieldResponse(
            field_path="empresa.cnpj",
            label="CNPJ",
            field_type="cnpj",
            important=True,
            required=True,
            raw_sample=cnpj,
            normalized_preview=str(normalized) if normalized is not None else None,
            display_value=display,
            confidence=0.9 if status == "valid" else 0.62,
        ))
        rules.append(SuggestedRuleResponse(
            field_path="empresa.cnpj",
            strategy=ExtractionStrategy.FIND_NEAR_LABEL,
            config={"label": "CNPJ", "position": "right"},
            confidence=0.86,
        ))

    competence = _best_raw_for_type(text, "month")
    if competence:
        normalized, display, status = _normalize_preview(competence, "month")
        fields.append(SuggestedFieldResponse(
            field_path="periodo.competencia",
            label="Competencia",
            field_type="month",
            important=True,
            required=True,
            raw_sample=competence,
            normalized_preview=str(normalized) if normalized is not None else None,
            display_value=display,
            confidence=0.84 if status == "valid" else 0.55,
        ))
        rules.append(SuggestedRuleResponse(
            field_path="periodo.competencia",
            strategy=ExtractionStrategy.REGEX_FROM_TEXT,
            config={"regex": r"(\d{1,2}/\d{4}|\d{4}-\d{1,2})"},
            confidence=0.8,
        ))

    if {"conta", "descricao"} <= headers or {"conta", "saldo"} <= headers:
        arrays.append(SuggestedArrayResponse(
            field_path="contas[]",
            label="Contas contabeis",
            item_fields=["contas[].codigo", "contas[].descricao", "contas[].saldo_atual"],
            confidence=0.82,
        ))
        fields.extend([
            SuggestedFieldResponse(field_path="contas[]", label="Contas contabeis", field_type="array", important=False, required=False, confidence=0.82),
            SuggestedFieldResponse(field_path="contas[].codigo", label="Codigo da conta", field_type="account_code", important=True, required=True, confidence=0.8),
            SuggestedFieldResponse(field_path="contas[].descricao", label="Descricao da conta", field_type="text", important=False, required=True, confidence=0.78),
            SuggestedFieldResponse(field_path="contas[].saldo_atual", label="Saldo atual", field_type="money", important=True, required=False, confidence=0.78),
        ])
        strategy = ExtractionStrategy.EXCEL_RANGE_TABLE if file_format in {"XLS", "XLSX"} else ExtractionStrategy.PDF_AREA_TABLE
        rules.append(SuggestedRuleResponse(
            field_path="contas[]",
            strategy=strategy,
            config={"headers": sorted(headers), "item_fields": ["contas[].codigo", "contas[].descricao", "contas[].saldo_atual"]},
            confidence=0.78,
        ))

    if not fields:
        warnings.append("Nenhum campo comum foi detectado com confianca suficiente no preview.")

    return TemplateSuggestionResponse(
        document_id=document_id,
        suggested_template=SuggestedTemplateResponse(
            name=f"Template {file_format}",
            category="Balancete" if headers else "Documento contabil",
            file_format=file_format,
            structure_type="table" if headers else "mixed",
        ),
        suggested_fields=fields,
        suggested_arrays=arrays,
        suggested_rules=rules,
        warnings=warnings,
    )


@router.post("/templates/{template_id}/rules/preview-normalization", response_model=RulePreviewNormalizationResponse)
async def preview_rule_normalization(
    template_id: str,
    payload: RulePreviewNormalizationRequest,
    service: TemplateServiceDep,
    document_service: DocumentServiceDep,
) -> RulePreviewNormalizationResponse:
    service.get_template(template_id, detail=False)
    preview_response = await document_service.get_preview(
        payload.document_id,
        authorization=service.principal.authorization,
        correlation_id=service.correlation_id,
    )
    if preview_response is None:
        raise NotFoundError("Document preview")
    preview = preview_response.get("preview") if isinstance(preview_response.get("preview"), dict) else preview_response
    raw_value, evidence, confidence = _find_value_for_rule(_text_items(preview), payload.field_type.value, payload.rule)
    normalized, display, status = _normalize_preview(raw_value, payload.field_type.value)
    evidence["field_path"] = payload.field_path
    return RulePreviewNormalizationResponse(
        field_path=payload.field_path,
        raw_value=raw_value,
        normalized_value=normalized,
        display_value=display,
        status=status,
        confidence=confidence if status == "valid" else min(confidence, 0.5),
        evidence=evidence,
    )

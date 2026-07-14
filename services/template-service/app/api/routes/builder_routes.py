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
    TemplateBuilderStateResponse,
    TemplateDetail,
    TemplateVersionResponse,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service
from app.domain.enums import TemplateVersionStatus


router = APIRouter(tags=["template-builder"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


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

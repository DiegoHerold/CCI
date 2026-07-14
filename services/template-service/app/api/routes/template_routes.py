from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.application.schemas import (
    TemplateCreate,
    TemplateDetail,
    TemplateListResponse,
    TemplateStatusUpdate,
    TemplateSummary,
    TemplateUpdate,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["templates"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates", response_model=TemplateSummary, status_code=201)
def create_template(payload: TemplateCreate, service: TemplateServiceDep) -> TemplateSummary:
    return TemplateSummary.from_entity(service.create_template(payload))


@router.get("/templates", response_model=TemplateListResponse)
def list_templates(
    service: TemplateServiceDep,
    category_id: str | None = None,
    file_format: str | None = None,
    status: str | None = None,
    structure_type: str | None = None,
    search: str | None = Query(default=None, min_length=1),
) -> TemplateListResponse:
    items, total = service.list_templates(
        category_id=category_id,
        file_format=file_format,
        status=status,
        structure_type=structure_type,
        search=search,
    )
    return TemplateListResponse(items=[TemplateSummary.from_entity(item) for item in items], total=total)


@router.get("/templates/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str, service: TemplateServiceDep) -> TemplateDetail:
    return TemplateDetail.from_entity(service.get_template(template_id))


@router.patch("/templates/{template_id}", response_model=TemplateSummary)
def update_template(template_id: str, payload: TemplateUpdate, service: TemplateServiceDep) -> TemplateSummary:
    return TemplateSummary.from_entity(service.update_template(template_id, payload))


@router.patch("/templates/{template_id}/status", response_model=TemplateSummary)
def update_template_status(
    template_id: str, payload: TemplateStatusUpdate, service: TemplateServiceDep
) -> TemplateSummary:
    return TemplateSummary.from_entity(service.update_template_status(template_id, payload.status))

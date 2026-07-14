from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.application.schemas import FieldCreate, FieldListResponse, FieldResponse, FieldUpdate
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["template-fields"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates/{template_id}/fields", response_model=FieldResponse, status_code=201)
def create_field(template_id: str, payload: FieldCreate, service: TemplateServiceDep) -> FieldResponse:
    return FieldResponse.from_entity(service.create_field(template_id, payload))


@router.get("/templates/{template_id}/fields", response_model=FieldListResponse)
def list_fields(template_id: str, service: TemplateServiceDep) -> FieldListResponse:
    return FieldListResponse(items=[FieldResponse.from_entity(item) for item in service.list_fields(template_id)])


@router.patch("/templates/{template_id}/fields/{field_id}", response_model=FieldResponse)
def update_field(
    template_id: str, field_id: str, payload: FieldUpdate, service: TemplateServiceDep
) -> FieldResponse:
    return FieldResponse.from_entity(service.update_field(template_id, field_id, payload))


@router.delete("/templates/{template_id}/fields/{field_id}", status_code=204)
def delete_field(template_id: str, field_id: str, service: TemplateServiceDep) -> Response:
    service.delete_field(template_id, field_id)
    return Response(status_code=204)

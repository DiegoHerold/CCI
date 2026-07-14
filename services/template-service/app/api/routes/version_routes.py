from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.schemas import (
    PublishVersionResponse,
    TemplateVersionCreate,
    TemplateVersionListResponse,
    TemplateVersionResponse,
)
from app.application.services import TemplateService
from app.domain.enums import TemplateVersionStatus
from app.dependencies import get_template_service


router = APIRouter(tags=["template-versions"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates/{template_id}/versions", response_model=TemplateVersionResponse, status_code=201)
def create_version(
    template_id: str, payload: TemplateVersionCreate, service: TemplateServiceDep
) -> TemplateVersionResponse:
    return TemplateVersionResponse.from_entity(service.create_version(template_id, payload.base_version_id))


@router.get("/templates/{template_id}/versions", response_model=TemplateVersionListResponse)
def list_versions(template_id: str, service: TemplateServiceDep) -> TemplateVersionListResponse:
    return TemplateVersionListResponse(
        items=[TemplateVersionResponse.from_entity(item) for item in service.list_versions(template_id)]
    )


@router.get("/templates/{template_id}/versions/{version_id}", response_model=TemplateVersionResponse)
def get_version(template_id: str, version_id: str, service: TemplateServiceDep) -> TemplateVersionResponse:
    return TemplateVersionResponse.from_entity(service.get_version(template_id, version_id))


@router.post("/templates/{template_id}/versions/{version_id}/publish", response_model=PublishVersionResponse)
def publish_version(template_id: str, version_id: str, service: TemplateServiceDep) -> PublishVersionResponse:
    version = service.publish_version(template_id, version_id)
    return PublishVersionResponse(
        template_id=template_id,
        version_id=version.id,
        version_number=version.version_number,
        status=TemplateVersionStatus(version.status),
        active=True,
    )


@router.post("/templates/{template_id}/versions/{version_id}/archive", response_model=TemplateVersionResponse)
def archive_version(template_id: str, version_id: str, service: TemplateServiceDep) -> TemplateVersionResponse:
    return TemplateVersionResponse.from_entity(service.archive_version(template_id, version_id))

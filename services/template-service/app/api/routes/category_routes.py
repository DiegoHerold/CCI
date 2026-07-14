from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.schemas import (
    TemplateCategoryCreate,
    TemplateCategoryListResponse,
    TemplateCategoryResponse,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["template-categories"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/template-categories", response_model=TemplateCategoryResponse, status_code=201)
def create_category(payload: TemplateCategoryCreate, service: TemplateServiceDep) -> TemplateCategoryResponse:
    return TemplateCategoryResponse.from_entity(service.create_category(payload))


@router.get("/template-categories", response_model=TemplateCategoryListResponse)
def list_categories(service: TemplateServiceDep) -> TemplateCategoryListResponse:
    return TemplateCategoryListResponse(
        items=[TemplateCategoryResponse.from_entity(item) for item in service.list_categories()]
    )


@router.get("/template-categories/{category_id}", response_model=TemplateCategoryResponse)
def get_category(category_id: str, service: TemplateServiceDep) -> TemplateCategoryResponse:
    return TemplateCategoryResponse.from_entity(service.get_category(category_id))

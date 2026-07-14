from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.application.schemas import AnnotationCreate, AnnotationListResponse, AnnotationResponse
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["template-annotations"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates/{template_id}/annotations", response_model=AnnotationResponse, status_code=201)
def create_annotation(
    template_id: str, payload: AnnotationCreate, service: TemplateServiceDep
) -> AnnotationResponse:
    return AnnotationResponse.from_entity(service.create_annotation(template_id, payload))


@router.get("/templates/{template_id}/annotations", response_model=AnnotationListResponse)
def list_annotations(
    template_id: str,
    service: TemplateServiceDep,
    field_id: str | None = None,
    document_id: str | None = None,
    annotation_type: str | None = None,
) -> AnnotationListResponse:
    return AnnotationListResponse(
        items=[
            AnnotationResponse.from_entity(item)
            for item in service.list_annotations(
                template_id,
                field_id=field_id,
                document_id=document_id,
                annotation_type=annotation_type,
            )
        ]
    )


@router.get("/templates/{template_id}/annotations/{annotation_id}", response_model=AnnotationResponse)
def get_annotation(template_id: str, annotation_id: str, service: TemplateServiceDep) -> AnnotationResponse:
    return AnnotationResponse.from_entity(service.get_annotation(template_id, annotation_id))


@router.delete("/templates/{template_id}/annotations/{annotation_id}", status_code=204)
def delete_annotation(template_id: str, annotation_id: str, service: TemplateServiceDep) -> Response:
    service.delete_annotation(template_id, annotation_id)
    return Response(status_code=204)

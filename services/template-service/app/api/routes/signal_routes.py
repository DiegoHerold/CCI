from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.application.schemas import (
    IdentificationSignalCreate,
    IdentificationSignalListResponse,
    IdentificationSignalResponse,
    IdentificationSignalUpdate,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["identification-signals"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post("/templates/{template_id}/identification-signals", response_model=IdentificationSignalResponse, status_code=201)
def create_signal(
    template_id: str, payload: IdentificationSignalCreate, service: TemplateServiceDep
) -> IdentificationSignalResponse:
    return IdentificationSignalResponse.from_entity(service.create_signal(template_id, payload))


@router.get("/templates/{template_id}/identification-signals", response_model=IdentificationSignalListResponse)
def list_signals(template_id: str, service: TemplateServiceDep) -> IdentificationSignalListResponse:
    return IdentificationSignalListResponse(
        items=[IdentificationSignalResponse.from_entity(item) for item in service.list_signals(template_id)]
    )


@router.patch("/templates/{template_id}/identification-signals/{signal_id}", response_model=IdentificationSignalResponse)
def update_signal(
    template_id: str, signal_id: str, payload: IdentificationSignalUpdate, service: TemplateServiceDep
) -> IdentificationSignalResponse:
    return IdentificationSignalResponse.from_entity(service.update_signal(template_id, signal_id, payload))


@router.delete("/templates/{template_id}/identification-signals/{signal_id}", status_code=204)
def delete_signal(template_id: str, signal_id: str, service: TemplateServiceDep) -> Response:
    service.delete_signal(template_id, signal_id)
    return Response(status_code=204)
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.application.schemas import (
    IdentificationSignalCreate,
    IdentificationSignalListResponse,
    IdentificationSignalResponse,
    IdentificationSignalUpdate,
)
from app.application.services import TemplateService
from app.dependencies import get_template_service


router = APIRouter(tags=["template-identification-signals"])
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post(
    "/templates/{template_id}/identification-signals",
    response_model=IdentificationSignalResponse,
    status_code=201,
)
def create_signal(
    template_id: str,
    payload: IdentificationSignalCreate,
    service: TemplateServiceDep,
) -> IdentificationSignalResponse:
    return IdentificationSignalResponse.from_entity(service.create_signal(template_id, payload))


@router.get(
    "/templates/{template_id}/identification-signals",
    response_model=IdentificationSignalListResponse,
)
def list_signals(
    template_id: str,
    service: TemplateServiceDep,
) -> IdentificationSignalListResponse:
    return IdentificationSignalListResponse(
        items=[IdentificationSignalResponse.from_entity(item) for item in service.list_signals(template_id)]
    )


@router.patch(
    "/templates/{template_id}/identification-signals/{signal_id}",
    response_model=IdentificationSignalResponse,
)
def update_signal(
    template_id: str,
    signal_id: str,
    payload: IdentificationSignalUpdate,
    service: TemplateServiceDep,
) -> IdentificationSignalResponse:
    return IdentificationSignalResponse.from_entity(
        service.update_signal(template_id, signal_id, payload)
    )


@router.delete("/templates/{template_id}/identification-signals/{signal_id}", status_code=204)
def delete_signal(template_id: str, signal_id: str, service: TemplateServiceDep) -> Response:
    service.delete_signal(template_id, signal_id)
    return Response(status_code=204)

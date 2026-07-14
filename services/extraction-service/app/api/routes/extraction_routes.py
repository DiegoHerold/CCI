from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.schemas import (
    ExtractionJobListResponse,
    ExtractionJobResponse,
    ExtractionReprocessRequest,
    ExtractionRequest,
    ExtractionResponse,
    ExtractionStatusResponse,
)
from app.application.services import ExtractionService
from app.config import Settings, get_settings
from app.dependencies import (
    CurrentPrincipal,
    get_artifact_storage,
    get_document_service,
    get_event_publisher,
    get_template_service,
    get_temporal_client,
    get_worker_dispatcher,
)
from app.infrastructure.clients.document_service import DocumentServiceHttpAdapter
from app.infrastructure.clients.template_service import TemplateServiceHttpAdapter
from app.infrastructure.database.session import get_db
from app.infrastructure.messaging.events import EventPublisher
from app.infrastructure.storage.artifact_storage import ArtifactStorage
from app.infrastructure.temporal.client import TemporalClient
from app.infrastructure.worker_dispatch import WorkerDispatcher


router = APIRouter(prefix="/extractions", tags=["extractions"])


def service_dependency(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    document_service: Annotated[DocumentServiceHttpAdapter, Depends(get_document_service)],
    template_service: Annotated[TemplateServiceHttpAdapter, Depends(get_template_service)],
    temporal_client: Annotated[TemporalClient, Depends(get_temporal_client)],
    dispatcher: Annotated[WorkerDispatcher, Depends(get_worker_dispatcher)],
    storage: Annotated[ArtifactStorage, Depends(get_artifact_storage)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> ExtractionService:
    return ExtractionService(
        session,
        settings,
        document_service,
        template_service,
        temporal_client,
        dispatcher,
        storage,
        publisher,
    )


ExtractionServiceDep = Annotated[ExtractionService, Depends(service_dependency)]


@router.post("/documents/{document_id}", response_model=ExtractionResponse)
async def request_document_extraction(
    document_id: str,
    payload: ExtractionRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResponse:
    job = await service.request_extraction_for_document(
        document_id,
        payload,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )
    return ExtractionResponse.from_entity(job)


@router.get("/jobs/{job_id}", response_model=ExtractionJobResponse)
def get_extraction_job(job_id: str, service: ExtractionServiceDep) -> ExtractionJobResponse:
    return ExtractionJobResponse.from_entity(service.get_job(job_id))


@router.get("/jobs/{job_id}/status", response_model=ExtractionStatusResponse)
def get_extraction_job_status(job_id: str, service: ExtractionServiceDep) -> ExtractionStatusResponse:
    return ExtractionStatusResponse.from_entity(service.get_job(job_id))


@router.get("/documents/{document_id}/jobs", response_model=ExtractionJobListResponse)
def list_document_extraction_jobs(document_id: str, service: ExtractionServiceDep) -> ExtractionJobListResponse:
    return ExtractionJobListResponse(
        items=[ExtractionJobResponse.from_entity(job) for job in service.list_jobs_for_document(document_id)]
    )


@router.get("/documents/{document_id}/latest", response_model=ExtractionJobResponse)
def get_latest_document_extraction(document_id: str, service: ExtractionServiceDep) -> ExtractionJobResponse:
    return ExtractionJobResponse.from_entity(service.latest_for_document(document_id))


@router.post("/documents/{document_id}/reprocess", response_model=ExtractionResponse)
async def reprocess_document_extraction(
    document_id: str,
    payload: ExtractionReprocessRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResponse:
    job = await service.reprocess_document(
        document_id,
        payload,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )
    return ExtractionResponse.from_entity(job)


@router.post("/jobs/{job_id}/retry", response_model=ExtractionResponse)
async def retry_extraction_job(
    job_id: str,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResponse:
    job = await service.retry_job(job_id, actor, getattr(request.state, "correlation_id", "system"))
    return ExtractionResponse.from_entity(job)


@router.post("/jobs/{job_id}/cancel", response_model=ExtractionResponse)
async def cancel_extraction_job(
    job_id: str,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResponse:
    job = await service.cancel_job(job_id, actor, getattr(request.state, "correlation_id", "system"))
    return ExtractionResponse.from_entity(job)

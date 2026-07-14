from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.schemas import (
    ExtractedArrayItemListResponse,
    ExtractedFieldListResponse,
    ExtractedFieldValueResponse,
    ExtractedObjectListResponse,
    ExtractedObjectResponse,
    ExtractionEvidenceListResponse,
    ExtractionEvidenceResponse,
    FieldCorrectionRequest,
    FieldReviewRequest,
    ExtractionJobListResponse,
    ExtractionJobResponse,
    ExtractionResultSummaryResponse,
    ExtractionReprocessRequest,
    ExtractionRequest,
    ExtractionResponse,
    ExtractionStatusResponse,
    NormalizationReprocessRequest,
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


@router.get("/jobs/{job_id}/result", response_model=ExtractionResultSummaryResponse)
def get_extraction_result_for_job(job_id: str, service: ExtractionServiceDep) -> ExtractionResultSummaryResponse:
    return ExtractionResultSummaryResponse.from_entity(service.get_result_for_job(job_id))


@router.get("/documents/{document_id}/result/latest", response_model=ExtractionResultSummaryResponse)
def get_latest_extraction_result_for_document(document_id: str, service: ExtractionServiceDep) -> ExtractionResultSummaryResponse:
    return ExtractionResultSummaryResponse.from_entity(service.latest_result_for_document(document_id))


@router.get("/results/{result_id}/fields", response_model=ExtractedFieldListResponse)
def list_extracted_fields(
    result_id: str,
    service: ExtractionServiceDep,
    field_path: str | None = None,
    status: str | None = None,
    field_type: str | None = None,
    requires_review: bool | None = None,
    min_confidence: float | None = None,
) -> ExtractedFieldListResponse:
    return ExtractedFieldListResponse(
        items=[
            ExtractedFieldValueResponse.from_entity(item)
            for item in service.list_result_fields(
                result_id,
                field_path=field_path,
                status=status,
                field_type=field_type,
                requires_review=requires_review,
                min_confidence=min_confidence,
            )
        ]
    )


@router.get("/results/{result_id}/fields/{field_value_id}", response_model=ExtractedFieldValueResponse)
def get_extracted_field(
    result_id: str,
    field_value_id: str,
    service: ExtractionServiceDep,
) -> ExtractedFieldValueResponse:
    return ExtractedFieldValueResponse.from_entity(service.get_result_field(result_id, field_value_id))


@router.get("/results/{result_id}/objects", response_model=ExtractedObjectListResponse)
def list_extracted_objects(result_id: str, service: ExtractionServiceDep) -> ExtractedObjectListResponse:
    return ExtractedObjectListResponse(
        items=[ExtractedObjectResponse.from_entity(item) for item in service.list_result_objects(result_id)]
    )


@router.get("/results/{result_id}/array-items", response_model=ExtractedArrayItemListResponse)
def list_extracted_array_items(
    result_id: str,
    field_path: str,
    service: ExtractionServiceDep,
) -> ExtractedArrayItemListResponse:
    return ExtractedArrayItemListResponse(
        items=[ExtractedArrayItemResponse.from_entity(item) for item in service.list_array_items(result_id, field_path)]
    )


@router.get("/fields/{field_value_id}/evidence", response_model=ExtractionEvidenceListResponse)
def list_field_evidence(field_value_id: str, service: ExtractionServiceDep) -> ExtractionEvidenceListResponse:
    return ExtractionEvidenceListResponse(
        items=[ExtractionEvidenceResponse.from_entity(item) for item in service.list_field_evidence(field_value_id)]
    )


@router.post("/jobs/{job_id}/normalize/reprocess", response_model=ExtractionResultSummaryResponse)
async def reprocess_job_normalization(
    job_id: str,
    payload: NormalizationReprocessRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResultSummaryResponse:
    result = await service.reprocess_normalization(
        job_id,
        actor,
        getattr(request.state, "correlation_id", "system"),
        payload.reason,
    )
    return ExtractionResultSummaryResponse.from_entity(result)


@router.patch("/fields/{field_value_id}/correction", response_model=ExtractedFieldValueResponse)
def correct_extracted_field(
    field_value_id: str,
    payload: FieldCorrectionRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractedFieldValueResponse:
    return ExtractedFieldValueResponse.from_entity(
        service.correct_field_value(
            field_value_id,
            payload.raw_value,
            actor,
            getattr(request.state, "correlation_id", "system"),
            payload.reason,
        )
    )


@router.post("/fields/{field_value_id}/approve", response_model=ExtractedFieldValueResponse)
def approve_extracted_field(
    field_value_id: str,
    payload: FieldReviewRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractedFieldValueResponse:
    return ExtractedFieldValueResponse.from_entity(
        service.approve_field_value(field_value_id, actor, getattr(request.state, "correlation_id", "system"), payload.reason)
    )


@router.post("/fields/{field_value_id}/reject", response_model=ExtractedFieldValueResponse)
def reject_extracted_field(
    field_value_id: str,
    payload: FieldReviewRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractedFieldValueResponse:
    return ExtractedFieldValueResponse.from_entity(
        service.reject_field_value(field_value_id, actor, getattr(request.state, "correlation_id", "system"), payload.reason)
    )


@router.post("/results/{result_id}/approve", response_model=ExtractionResultSummaryResponse)
def approve_extraction_result(
    result_id: str,
    payload: FieldReviewRequest,
    request: Request,
    actor: CurrentPrincipal,
    service: ExtractionServiceDep,
) -> ExtractionResultSummaryResponse:
    return ExtractionResultSummaryResponse.from_entity(
        service.approve_result(result_id, actor, getattr(request.state, "correlation_id", "system"), payload.reason)
    )

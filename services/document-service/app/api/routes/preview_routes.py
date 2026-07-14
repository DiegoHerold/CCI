from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.context import RequestContext, context_from_request
from app.application.preview_service import PreviewService
from app.application.schemas import (
    DocumentPreviewResponse,
    DocumentPreviewStatusResponse,
    PreviewRequestResponse,
)
from app.config import Settings, get_settings
from app.dependencies import (
    CurrentPrincipal,
    get_client_adapter,
    get_event_publisher,
    get_parser_worker_client,
    get_storage_client,
)
from app.infrastructure.client_gateway import ClientServiceHttpAdapter
from app.infrastructure.database.session import get_db
from app.infrastructure.events import EventPublisher
from app.infrastructure.parser_worker import ParserWorkerClient
from app.infrastructure.storage import StorageClient


router = APIRouter(prefix="/documents/{document_id}/preview", tags=["document-preview"])


def _context(request: Request) -> RequestContext:
    return context_from_request(request)


def _service(
    session: Session,
    settings: Settings,
    storage: StorageClient,
    publisher: EventPublisher,
    parser_worker: ParserWorkerClient,
) -> PreviewService:
    return PreviewService(session, settings, storage, publisher, parser_worker)


async def _validate_document_access(
    document_id: str,
    request: Request,
    service: PreviewService,
    client_adapter: ClientServiceHttpAdapter,
    actor: CurrentPrincipal,
) -> None:
    document = service._get_document(document_id)
    await client_adapter.validate_competence(
        document.client_id,
        document.competence_id,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )


@router.post("", response_model=PreviewRequestResponse)
async def request_preview(
    document_id: str,
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    parser_worker: Annotated[ParserWorkerClient, Depends(get_parser_worker_client)],
) -> PreviewRequestResponse:
    service = _service(session, settings, storage, publisher, parser_worker)
    await _validate_document_access(document_id, request, service, client_adapter, actor)
    response = service.create_preview_job(document_id, actor, _context(request))
    await service.process_job(response.parsing_job_id, actor, _context(request))
    return response


@router.get("/status", response_model=DocumentPreviewStatusResponse)
async def get_preview_status(
    document_id: str,
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    parser_worker: Annotated[ParserWorkerClient, Depends(get_parser_worker_client)],
) -> DocumentPreviewStatusResponse:
    service = _service(session, settings, storage, publisher, parser_worker)
    await _validate_document_access(document_id, request, service, client_adapter, actor)
    return service.get_status(document_id)


@router.get("", response_model=DocumentPreviewResponse)
async def get_preview(
    document_id: str,
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    parser_worker: Annotated[ParserWorkerClient, Depends(get_parser_worker_client)],
) -> DocumentPreviewResponse:
    service = _service(session, settings, storage, publisher, parser_worker)
    await _validate_document_access(document_id, request, service, client_adapter, actor)
    return service.get_preview(document_id)


@router.post("/reprocess", response_model=PreviewRequestResponse)
async def reprocess_preview(
    document_id: str,
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    parser_worker: Annotated[ParserWorkerClient, Depends(get_parser_worker_client)],
) -> PreviewRequestResponse:
    service = _service(session, settings, storage, publisher, parser_worker)
    await _validate_document_access(document_id, request, service, client_adapter, actor)
    response = service.create_preview_job(document_id, actor, _context(request))
    await service.process_job(response.parsing_job_id, actor, _context(request))
    return response

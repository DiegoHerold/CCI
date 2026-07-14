from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.application.schemas import DocumentResponse, DocumentStatusUpdate
from app.application.services import DocumentService
from app.config import Settings, get_settings
from app.dependencies import (
    CurrentPrincipal,
    get_client_adapter,
    get_event_publisher,
    get_storage_client,
)
from app.infrastructure.client_gateway import ClientServiceHttpAdapter
from app.infrastructure.database.session import get_db
from app.infrastructure.events import EventPublisher
from app.infrastructure.storage import StorageClient


router = APIRouter(prefix="/documents", tags=["documents"])


@router.patch("/{document_id}/status", response_model=DocumentResponse)
async def update_document_status(
    document_id: str,
    request: Request,
    payload: DocumentStatusUpdate,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> DocumentResponse:
    service = DocumentService(session, settings, storage, publisher)
    current = service.get(document_id)
    await client_adapter.validate_competence(
        current.client_id,
        current.competence_id,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )
    document = service.change_status(
        document_id,
        payload.status,
        payload.reason,
        actor,
    )
    return DocumentResponse.from_entity(document)

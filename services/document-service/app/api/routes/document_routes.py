from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.application.schemas import DocumentListResponse, DocumentResponse
from app.application.services import DocumentService
from app.config import Settings, get_settings
from app.dependencies import (
    CurrentPrincipal,
    get_client_adapter,
    get_event_publisher,
    get_storage_client,
)
from app.domain.enums import DocumentStatus, FileFormat
from app.infrastructure.client_gateway import ClientServiceHttpAdapter
from app.infrastructure.database.session import get_db
from app.infrastructure.events import EventPublisher
from app.infrastructure.storage import StorageClient


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> DocumentResponse:
    document = DocumentService(session, settings, storage, publisher).get(document_id)
    await client_adapter.validate_competence(
        document.client_id,
        document.competence_id,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )
    return DocumentResponse.from_entity(document)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    client_id: str | None = None,
    competence_id: str | None = None,
    status_filter: Annotated[DocumentStatus | None, Query(alias="status")] = None,
    file_format: Annotated[FileFormat | None, Query(alias="fileFormat")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentListResponse:
    if client_id and competence_id:
        await client_adapter.validate_competence(
            client_id,
            competence_id,
            actor,
            getattr(request.state, "correlation_id", "system"),
        )
    elif client_id:
        await client_adapter.validate_client(
            client_id,
            actor,
            getattr(request.state, "correlation_id", "system"),
        )
    items, total = DocumentService(session, settings, storage, publisher).list(
        client_id=client_id,
        competence_id=competence_id,
        status=status_filter,
        file_format=file_format.value if file_format else None,
        page=page,
        limit=limit,
    )
    return DocumentListResponse(
        items=[DocumentResponse.from_entity(item) for item in items],
        page=page,
        limit=limit,
        total=total,
    )

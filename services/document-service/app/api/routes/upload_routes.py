from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.application.context import context_from_request
from app.application.schemas import DocumentResponse, UploadZipResponse
from app.application.services import UploadCandidate, UploadService
from app.config import Settings, get_settings
from app.dependencies import (
    CurrentPrincipal,
    get_client_adapter,
    get_event_publisher,
    get_storage_client,
)
from app.infrastructure.client_gateway import ClientServiceHttpAdapter
from app.infrastructure.events import EventPublisher
from app.infrastructure.storage import StorageClient
from app.infrastructure.database.session import get_db


router = APIRouter(prefix="/documents", tags=["documents"])


async def _validate_client_context(
    *,
    client_id: str,
    competence_id: str,
    actor: CurrentPrincipal,
    adapter: ClientServiceHttpAdapter,
    request: Request,
) -> None:
    await adapter.validate_competence(
        client_id,
        competence_id,
        actor,
        getattr(request.state, "correlation_id", "system"),
    )


async def _candidate_from_upload(file: UploadFile) -> UploadCandidate:
    content = await file.read()
    return UploadCandidate(
        filename=file.filename or "upload.bin",
        content=content,
        content_type=file.content_type,
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File()],
    client_id: Annotated[str, Form()],
    competence_id: Annotated[str, Form()],
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> DocumentResponse:
    await _validate_client_context(
        client_id=client_id,
        competence_id=competence_id,
        actor=actor,
        adapter=client_adapter,
        request=request,
    )
    return UploadService(session, settings, storage, publisher).upload_single(
        client_id=client_id,
        competence_id=competence_id,
        candidate=await _candidate_from_upload(file),
        actor=actor,
        context=context_from_request(request),
    )


@router.post("/upload-zip", response_model=UploadZipResponse)
async def upload_zip(
    request: Request,
    file: Annotated[UploadFile, File()],
    client_id: Annotated[str, Form()],
    competence_id: Annotated[str, Form()],
    actor: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    client_adapter: Annotated[ClientServiceHttpAdapter, Depends(get_client_adapter)],
    storage: Annotated[StorageClient, Depends(get_storage_client)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
) -> UploadZipResponse:
    await _validate_client_context(
        client_id=client_id,
        competence_id=competence_id,
        actor=actor,
        adapter=client_adapter,
        request=request,
    )
    return UploadService(session, settings, storage, publisher).upload_zip(
        client_id=client_id,
        competence_id=competence_id,
        candidate=await _candidate_from_upload(file),
        actor=actor,
        context=context_from_request(request),
    )

from typing import Annotated

from fastapi import Depends, Header, Request

from app.config import Settings, get_settings
from app.infrastructure.clients.document_service import DocumentServiceHttpAdapter
from app.infrastructure.clients.template_service import TemplateServiceHttpAdapter
from app.infrastructure.identity_gateway import IdentityGateway, Principal
from app.infrastructure.messaging.events import EventPublisher, NoOpEventPublisher
from app.infrastructure.storage.artifact_storage import ArtifactStorage
from app.infrastructure.temporal.client import TemporalClient
from app.infrastructure.worker_dispatch import WorkerDispatcher


def settings_dependency() -> Settings:
    return get_settings()


def get_identity_gateway(settings: Annotated[Settings, Depends(get_settings)]) -> IdentityGateway:
    return IdentityGateway(settings)


async def current_principal(
    request: Request,
    gateway: Annotated[IdentityGateway, Depends(get_identity_gateway)],
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    return await gateway.authenticate(authorization, getattr(request.state, "correlation_id", "system"))


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]


def get_document_service(settings: Annotated[Settings, Depends(get_settings)]) -> DocumentServiceHttpAdapter:
    return DocumentServiceHttpAdapter(settings)


def get_template_service(settings: Annotated[Settings, Depends(get_settings)]) -> TemplateServiceHttpAdapter:
    return TemplateServiceHttpAdapter(settings)


def get_event_publisher() -> EventPublisher:
    return NoOpEventPublisher()


def get_artifact_storage(settings: Annotated[Settings, Depends(get_settings)]) -> ArtifactStorage:
    return ArtifactStorage(settings)


def get_temporal_client(settings: Annotated[Settings, Depends(get_settings)]) -> TemporalClient:
    return TemporalClient(settings)


def get_worker_dispatcher(settings: Annotated[Settings, Depends(get_settings)]) -> WorkerDispatcher:
    return WorkerDispatcher(
        pdf_task_queue=settings.pdf_extractor_worker_task_queue,
        excel_task_queue=settings.excel_extractor_worker_task_queue,
        pdf_worker_url=settings.pdf_extractor_worker_url,
        excel_worker_url=settings.excel_extractor_worker_url,
        timeout_seconds=settings.extractor_worker_timeout_seconds,
    )

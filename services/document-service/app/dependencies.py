from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.errors import InvalidTokenError
from app.infrastructure.client_gateway import ClientServiceHttpAdapter
from app.infrastructure.database.session import get_db
from app.infrastructure.events import EventPublisher, NoOpEventPublisher
from app.infrastructure.identity_gateway import IdentityGateway, Principal
from app.infrastructure.parser_worker import HttpParserWorkerClient, ParserWorkerClient
from app.infrastructure.storage import S3DocumentStorage, StorageClient


def get_identity_gateway(
    settings: Annotated[Settings, Depends(get_settings)],
) -> IdentityGateway:
    return IdentityGateway(settings)


async def get_current_principal(
    request: Request,
    identity: Annotated[IdentityGateway, Depends(get_identity_gateway)],
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise InvalidTokenError()
    return await identity.authenticate(
        authorization, getattr(request.state, "correlation_id", "system")
    )


def get_client_adapter(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientServiceHttpAdapter:
    return ClientServiceHttpAdapter(settings)


def get_storage_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StorageClient:
    return S3DocumentStorage(settings)


def get_event_publisher() -> EventPublisher:
    return NoOpEventPublisher()


def get_parser_worker_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ParserWorkerClient:
    return HttpParserWorkerClient(settings)


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
DatabaseSession = Annotated[Session, Depends(get_db)]

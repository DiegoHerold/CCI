from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.errors import InvalidTokenError
from app.application.services import TemplateService
from app.infrastructure.database.session import get_db
from app.infrastructure.document_service import DocumentServiceHttpAdapter, DocumentServicePort
from app.infrastructure.events import EventPublisher, NoOpEventPublisher
from app.infrastructure.identity_gateway import IdentityGateway, Principal


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


def get_event_publisher() -> EventPublisher:
    return NoOpEventPublisher()


def get_document_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentServicePort:
    return DocumentServiceHttpAdapter(settings)


def get_template_service(
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    principal: Annotated[Principal, Depends(get_current_principal)],
) -> TemplateService:
    return TemplateService(
        session=session,
        settings=settings,
        publisher=publisher,
        principal=principal,
        correlation_id=getattr(request.state, "correlation_id", "system"),
    )


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]
DatabaseSession = Annotated[Session, Depends(get_db)]

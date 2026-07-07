from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.application.context import context_from_request
from app.application.services import ClientAccessService
from app.config import Settings, get_settings
from app.errors import ForbiddenError, InvalidTokenError
from app.infrastructure.database.models import ClientUser
from app.infrastructure.database.session import get_db
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


CurrentPrincipal = Annotated[Principal, Depends(get_current_principal)]


def require_permission(permission: str) -> Callable[..., Principal]:
    def dependency(principal: CurrentPrincipal) -> Principal:
        if permission not in principal.permissions:
            raise ForbiddenError()
        return principal

    return dependency


def require_client_access(
    client_id: str,
    request: Request,
    principal: CurrentPrincipal,
    session: Annotated[Session, Depends(get_db)],
) -> ClientUser | None:
    return ClientAccessService(session).require(
        principal, client_id, context_from_request(request)
    )


ClientAccess = Annotated[ClientUser | None, Depends(require_client_access)]

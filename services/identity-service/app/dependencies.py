from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.audit import IdentityAuditService
from app.application.context import context_from_request
from app.application.security import decode_access_token, ensure_utc, utc_now
from app.config import Settings, get_settings
from app.domain.access import PermissionName, RoleName, UserStatus
from app.domain.audit import IdentityAuditEventType
from app.errors import ForbiddenError, InvalidTokenError
from app.infrastructure.database.models import User
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import (
    AuthSessionRepository,
    UserRepository,
    get_permission_names,
    get_role_names,
)


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    user: User
    session_id: str
    claims: dict[str, Any]


def get_current_principal(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedPrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError()
    payload = decode_access_token(credentials.credentials, settings)
    auth_session = AuthSessionRepository(session).get_by_id(payload["sid"])
    if auth_session is None or auth_session.user_id != payload["sub"]:
        raise InvalidTokenError()
    if auth_session.revoked_at is not None:
        raise InvalidTokenError()
    if ensure_utc(auth_session.expires_at) <= utc_now():
        raise InvalidTokenError()
    user = UserRepository(session).get_by_id(payload["sub"])
    if user is None or user.status != UserStatus.ACTIVE.value:
        raise InvalidTokenError()
    return AuthenticatedPrincipal(user, auth_session.id, payload)


Principal = Annotated[AuthenticatedPrincipal, Depends(get_current_principal)]


def get_current_user(principal: Principal) -> User:
    return principal.user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(role: RoleName) -> Callable[..., User]:
    def dependency(current_user: CurrentUser) -> User:
        if role.value not in get_role_names(current_user):
            raise ForbiddenError(f"Role {role.value} is required")
        return current_user

    return dependency


def require_permission(permission: PermissionName) -> Callable[..., User]:
    def dependency(
        request: Request,
        current_user: CurrentUser,
        session: Annotated[Session, Depends(get_db)],
    ) -> User:
        if permission.value not in get_permission_names(current_user):
            IdentityAuditService(session).record(
                IdentityAuditEventType.AUTH_PERMISSION_DENIED,
                context_from_request(request),
                user_id=current_user.id,
                metadata={
                    "requiredPermission": permission.value,
                    "path": request.url.path,
                },
            )
            session.commit()
            raise ForbiddenError()
        return current_user

    return dependency

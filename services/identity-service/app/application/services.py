from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.schemas import UserCreate, UserUpdate
from app.application.security import (
    hash_password,
    utc_now,
    validate_password_policy,
)
from app.application.audit import IdentityAuditService
from app.application.context import RequestContext
from app.domain.access import UserStatus
from app.domain.audit import IdentityAuditEventType
from app.errors import ConflictError, NotFoundError
from app.infrastructure.database.models import User
from app.infrastructure.repositories import AuthSessionRepository, UserRepository


class IdentityService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)

    def get_user(self, user_id: str) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError()
        return user

    def list_users(self) -> list[User]:
        return self.users.list_all()

    def _roles(self, role_names: set[str]):
        roles = self.users.get_roles(role_names)
        if {role.name for role in roles} != role_names:
            raise ValueError("one or more roles are not initialized")
        return roles

    def create_user(self, payload: UserCreate) -> User:
        email = str(payload.email).strip().lower()
        if self.users.get_by_email(email) is not None:
            raise ConflictError("Email is already registered")
        validate_password_policy(payload.password, payload.name, email)
        user = User(
            name=payload.name,
            email=email,
            password_hash=hash_password(payload.password),
            status=UserStatus.ACTIVE.value,
            roles=self._roles({role.value for role in payload.roles}),
        )
        try:
            self.users.add(user)
            self.users.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Email is already registered") from exc
        return user

    def update_user(
        self,
        user_id: str,
        payload: UserUpdate,
        actor: User | None = None,
        context: RequestContext | None = None,
    ) -> User:
        user = self.get_user(user_id)
        previous_status = user.status
        if payload.name is not None:
            user.name = payload.name
        if payload.email is not None:
            email = str(payload.email).strip().lower()
            existing = self.users.get_by_email(email)
            if existing is not None and existing.id != user.id:
                raise ConflictError("Email is already registered")
            user.email = email
        if payload.roles is not None:
            user.roles = self._roles({role.value for role in payload.roles})
        if payload.status is not None:
            user.status = payload.status.value
        if previous_status != user.status and context is not None:
            event_type = (
                IdentityAuditEventType.AUTH_USER_ENABLED
                if user.status == UserStatus.ACTIVE.value
                else IdentityAuditEventType.AUTH_USER_DISABLED
            )
            if user.status == UserStatus.INACTIVE.value:
                AuthSessionRepository(self.session).revoke_all(user.id, utc_now())
            IdentityAuditService(self.session).record(
                event_type,
                context,
                user_id=user.id,
                metadata={"actorUserId": actor.id if actor else None},
            )
        try:
            self.users.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ConflictError("Email is already registered") from exc
        return user

    def disable_user(
        self, user_id: str, actor: User, context: RequestContext
    ) -> User:
        return self.update_user(
            user_id,
            UserUpdate(status=UserStatus.INACTIVE),
            actor=actor,
            context=context,
        )

    def reset_password(
        self,
        user_id: str,
        new_password: str,
        actor: User,
        context: RequestContext,
    ) -> User:
        user = self.get_user(user_id)
        validate_password_policy(new_password, user.name, user.email)
        user.password_hash = hash_password(new_password)
        revoked = AuthSessionRepository(self.session).revoke_all(
            user.id, utc_now()
        )
        IdentityAuditService(self.session).record(
            IdentityAuditEventType.AUTH_PASSWORD_RESET_BY_ADMIN,
            context,
            user_id=user.id,
            metadata={"actorUserId": actor.id, "revokedSessions": revoked},
        )
        self.users.commit()
        return user

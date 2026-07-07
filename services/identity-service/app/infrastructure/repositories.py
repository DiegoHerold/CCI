from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.database.models import (
    AuthSession,
    IdentityAuditEvent,
    LoginRateLimit,
    Role,
    User,
)


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _with_access():
        return selectinload(User.roles).selectinload(Role.permissions)

    def get_by_id(self, user_id: str) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(self._with_access())
        )
        return self.session.scalar(statement)

    def get_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .where(User.email == email.strip().lower())
            .options(self._with_access())
        )
        return self.session.scalar(statement)

    def list_all(self) -> list[User]:
        statement = select(User).options(self._with_access()).order_by(User.name)
        return list(self.session.scalars(statement).all())

    def get_roles(self, names: set[str]) -> list[Role]:
        statement = select(Role).where(Role.name.in_(names)).options(
            selectinload(Role.permissions)
        )
        return list(self.session.scalars(statement).all())

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user

    def commit(self) -> None:
        self.session.commit()


class AuthSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, session_id: str) -> AuthSession | None:
        return self.session.get(AuthSession, session_id)

    def add(self, auth_session: AuthSession) -> AuthSession:
        self.session.add(auth_session)
        self.session.flush()
        return auth_session

    def revoke(self, auth_session: AuthSession, revoked_at: datetime) -> None:
        if auth_session.revoked_at is None:
            auth_session.revoked_at = revoked_at

    def revoke_all(
        self,
        user_id: str,
        revoked_at: datetime,
        except_session_id: str | None = None,
    ) -> int:
        statement = (
            update(AuthSession)
            .where(
                AuthSession.user_id == user_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at, updated_at=revoked_at)
        )
        if except_session_id is not None:
            statement = statement.where(AuthSession.id != except_session_id)
        result = self.session.execute(statement)
        return int(result.rowcount or 0)


class AuditRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: IdentityAuditEvent) -> None:
        self.session.add(event)


class LoginRateLimitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_update(self, identifier_hash: str) -> LoginRateLimit | None:
        statement = (
            select(LoginRateLimit)
            .where(LoginRateLimit.identifier_hash == identifier_hash)
            .with_for_update()
        )
        return self.session.scalar(statement)

    def add(self, entry: LoginRateLimit) -> None:
        self.session.add(entry)


def get_permission_names(user: User) -> list[str]:
    return sorted(
        {
            permission.name
            for role in user.roles
            for permission in role.permissions
        }
    )


def get_role_names(user: User) -> list[str]:
    return sorted(role.name for role in user.roles)

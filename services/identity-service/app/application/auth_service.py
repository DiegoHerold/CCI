from dataclasses import dataclass
from datetime import timedelta
import hashlib
from uuid import uuid4

from sqlalchemy.orm import Session

from app.application.audit import IdentityAuditService
from app.application.context import RequestContext
from app.application.rate_limit import LoginRateLimiter
from app.application.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    ensure_utc,
    hash_password,
    hash_refresh_token,
    refresh_token_matches,
    utc_now,
    validate_password_policy,
    verify_dummy_password,
    verify_password,
)
from app.config import Settings
from app.domain.access import UserStatus
from app.domain.audit import IdentityAuditEventType
from app.errors import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RateLimitExceededError,
)
from app.infrastructure.database.models import AuthSession, User
from app.infrastructure.repositories import AuthSessionRepository, UserRepository


@dataclass(frozen=True)
class LoginResult:
    user: User
    access_token: str
    refresh_token: str


def _safe_email_fingerprint(email: str) -> str:
    return hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()[:16]


class AuthenticationService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.sessions = AuthSessionRepository(session)
        self.audit = IdentityAuditService(session)

    def _record_login_failure(
        self,
        context: RequestContext,
        email: str,
        user: User | None,
        reason: str,
    ) -> None:
        metadata = {
            "reason": reason,
            "emailFingerprint": _safe_email_fingerprint(email),
        }
        if user is not None:
            metadata["failedAttempts"] = user.failed_login_attempts
        self.audit.record(
            IdentityAuditEventType.AUTH_LOGIN_FAILED,
            context,
            user_id=user.id if user else None,
            metadata=metadata,
        )

    def login(
        self, email: str, password: str, context: RequestContext
    ) -> LoginResult:
        try:
            LoginRateLimiter(self.session, self.settings).consume(
                context.ip_address, email
            )
            self.session.commit()
        except RateLimitExceededError:
            user = self.users.get_by_email(email)
            self._record_login_failure(context, email, user, "rate_limited")
            self.session.commit()
            raise

        now = utc_now()
        user = self.users.get_by_email(email)
        if user is None:
            verify_dummy_password(password)
            self._record_login_failure(context, email, None, "invalid_credentials")
            self.session.commit()
            raise InvalidCredentialsError()

        if user.locked_until is not None and ensure_utc(user.locked_until) > now:
            self._record_login_failure(context, email, user, "temporarily_locked")
            self.session.commit()
            raise InvalidCredentialsError()
        if user.locked_until is not None:
            user.failed_login_attempts = 0
            user.locked_until = None

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            user.last_failed_login_at = now
            if user.failed_login_attempts >= self.settings.auth_max_failed_attempts:
                user.locked_until = now + timedelta(
                    minutes=self.settings.auth_lock_minutes
                )
            self._record_login_failure(context, email, user, "invalid_credentials")
            self.session.commit()
            raise InvalidCredentialsError()

        if user.status != UserStatus.ACTIVE.value:
            self._record_login_failure(context, email, user, "unavailable_account")
            self.session.commit()
            raise InvalidCredentialsError()

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_failed_login_at = None
        auth_session_id = str(uuid4())
        refresh_token = create_refresh_token(
            user, auth_session_id, self.settings
        )
        auth_session = AuthSession(
            id=auth_session_id,
            user_id=user.id,
            refresh_token_hash=hash_refresh_token(refresh_token),
            user_agent=context.user_agent,
            ip_address=context.ip_address,
            expires_at=now
            + timedelta(seconds=self.settings.jwt_refresh_expires_in),
        )
        self.sessions.add(auth_session)
        self.audit.record(
            IdentityAuditEventType.AUTH_LOGIN_SUCCESS,
            context,
            user_id=user.id,
            metadata={"sessionId": auth_session.id},
        )
        access_token = create_access_token(user, auth_session.id, self.settings)
        self.session.commit()
        return LoginResult(user, access_token, refresh_token)

    def _validated_refresh_session(
        self, refresh_token: str
    ) -> tuple[AuthSession, User]:
        payload = decode_refresh_token(refresh_token, self.settings)
        auth_session = self.sessions.get_by_id(payload["sid"])
        if auth_session is None or auth_session.user_id != payload["sub"]:
            raise InvalidRefreshTokenError()
        if auth_session.revoked_at is not None:
            raise InvalidRefreshTokenError()
        if ensure_utc(auth_session.expires_at) <= utc_now():
            raise InvalidRefreshTokenError()
        if not refresh_token_matches(
            refresh_token, auth_session.refresh_token_hash
        ):
            raise InvalidRefreshTokenError()
        user = self.users.get_by_id(auth_session.user_id)
        if user is None or user.status != UserStatus.ACTIVE.value:
            raise InvalidRefreshTokenError()
        return auth_session, user

    def refresh(self, refresh_token: str, context: RequestContext) -> str:
        auth_session, user = self._validated_refresh_session(refresh_token)
        self.audit.record(
            IdentityAuditEventType.AUTH_TOKEN_REFRESH,
            context,
            user_id=user.id,
            metadata={"sessionId": auth_session.id},
        )
        access_token = create_access_token(user, auth_session.id, self.settings)
        self.session.commit()
        return access_token

    def logout(
        self,
        user: User,
        session_id: str,
        context: RequestContext,
        refresh_token: str | None = None,
    ) -> None:
        auth_session = self.sessions.get_by_id(session_id)
        if auth_session is None or auth_session.user_id != user.id:
            raise InvalidRefreshTokenError()
        self.sessions.revoke(auth_session, utc_now())
        self.audit.record(
            IdentityAuditEventType.AUTH_LOGOUT,
            context,
            user_id=user.id,
            metadata={
                "sessionId": session_id,
                "refreshTokenProvided": refresh_token is not None,
            },
        )
        self.session.commit()

    def logout_all(self, user: User, context: RequestContext) -> None:
        revoked = self.sessions.revoke_all(user.id, utc_now())
        self.audit.record(
            IdentityAuditEventType.AUTH_LOGOUT_ALL,
            context,
            user_id=user.id,
            metadata={"revokedSessions": revoked},
        )
        self.session.commit()

    def change_password(
        self,
        user: User,
        current_session_id: str,
        current_password: str,
        new_password: str,
        context: RequestContext,
    ) -> None:
        if not verify_password(current_password, user.password_hash):
            raise InvalidCredentialsError()
        validate_password_policy(new_password, user.name, user.email)
        user.password_hash = hash_password(new_password)
        revoked = self.sessions.revoke_all(
            user.id, utc_now(), except_session_id=current_session_id
        )
        self.audit.record(
            IdentityAuditEventType.AUTH_PASSWORD_CHANGED,
            context,
            user_id=user.id,
            metadata={
                "currentSessionPreserved": True,
                "revokedSessions": revoked,
            },
        )
        self.session.commit()

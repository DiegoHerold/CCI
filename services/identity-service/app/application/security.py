from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from typing import Any
from uuid import uuid4

import jwt
from jwt import InvalidTokenError as PyJwtInvalidTokenError
from pwdlib import PasswordHash

from app.config import Settings
from app.errors import InvalidRefreshTokenError, InvalidTokenError, PasswordPolicyError
from app.infrastructure.database.models import User
from app.infrastructure.repositories import get_permission_names, get_role_names


password_hasher = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = password_hasher.hash("cci-invalid-credential-sentinel")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def verify_dummy_password(password: str) -> None:
    verify_password(password, _DUMMY_PASSWORD_HASH)


def validate_password_policy(password: str, name: str, email: str) -> None:
    normalized = password.strip().casefold()
    if len(password) < 8:
        raise PasswordPolicyError()
    if not any(character.isalpha() for character in password):
        raise PasswordPolicyError()
    if not any(character.isdigit() for character in password):
        raise PasswordPolicyError()
    if normalized in {name.strip().casefold(), email.strip().casefold()}:
        raise PasswordPolicyError()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def refresh_token_matches(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(hash_refresh_token(token), expected_hash)


def _encode_token(
    user: User,
    session_id: str,
    settings: Settings,
    token_type: str,
    expires_in: int,
) -> str:
    now = utc_now()
    payload: dict[str, Any] = {
        "sub": user.id,
        "sid": session_id,
        "typ": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    if token_type == "access":
        payload.update(
            {
                "email": user.email,
                "roles": get_role_names(user),
                "permissions": get_permission_names(user),
            }
        )
        secret = settings.jwt_access_secret.get_secret_value()
    else:
        secret = settings.jwt_refresh_secret.get_secret_value()
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def create_access_token(user: User, session_id: str, settings: Settings) -> str:
    return _encode_token(
        user,
        session_id,
        settings,
        "access",
        settings.jwt_access_expires_in,
    )


def create_refresh_token(user: User, session_id: str, settings: Settings) -> str:
    return _encode_token(
        user,
        session_id,
        settings,
        "refresh",
        settings.jwt_refresh_expires_in,
    )


def _decode_token(
    token: str,
    secret: str,
    algorithm: str,
    token_type: str,
) -> dict[str, Any]:
    required = ["sub", "sid", "typ", "jti", "iat", "exp"]
    if token_type == "access":
        required.extend(["email", "roles", "permissions"])
    payload = jwt.decode(
        token,
        secret,
        algorithms=[algorithm],
        options={"require": required},
    )
    if payload.get("typ") != token_type:
        raise PyJwtInvalidTokenError("unexpected token type")
    if not isinstance(payload.get("sub"), str):
        raise PyJwtInvalidTokenError("invalid subject")
    if not isinstance(payload.get("sid"), str):
        raise PyJwtInvalidTokenError("invalid session")
    return payload


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = _decode_token(
            token,
            settings.jwt_access_secret.get_secret_value(),
            settings.jwt_algorithm,
            "access",
        )
    except PyJwtInvalidTokenError as exc:
        raise InvalidTokenError() from exc
    if not isinstance(payload.get("roles"), list):
        raise InvalidTokenError()
    if not isinstance(payload.get("permissions"), list):
        raise InvalidTokenError()
    return payload


def decode_refresh_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        return _decode_token(
            token,
            settings.jwt_refresh_secret.get_secret_value(),
            settings.jwt_algorithm,
            "refresh",
        )
    except PyJwtInvalidTokenError as exc:
        raise InvalidRefreshTokenError() from exc

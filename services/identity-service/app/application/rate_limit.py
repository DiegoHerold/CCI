from datetime import timedelta
import hashlib

from sqlalchemy.orm import Session

from app.application.security import ensure_utc, utc_now
from app.config import Settings
from app.errors import RateLimitExceededError
from app.infrastructure.database.models import LoginRateLimit
from app.infrastructure.repositories import LoginRateLimitRepository


def _identifier_hash(kind: str, value: str) -> str:
    normalized = value.strip().casefold()
    return hashlib.sha256(f"{kind}:{normalized}".encode("utf-8")).hexdigest()


class LoginRateLimiter:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.repository = LoginRateLimitRepository(session)
        self.settings = settings

    def consume(self, ip_address: str | None, email: str) -> None:
        now = utc_now()
        identifiers = {
            _identifier_hash("ip", ip_address or "unknown"),
            _identifier_hash("email", email),
        }
        entries: list[LoginRateLimit] = []
        for identifier in identifiers:
            entry = self.repository.get_for_update(identifier)
            if entry is None:
                entry = LoginRateLimit(
                    identifier_hash=identifier,
                    attempts=0,
                    window_started_at=now,
                )
                self.repository.add(entry)
            elif now - ensure_utc(entry.window_started_at) >= timedelta(
                seconds=self.settings.auth_login_rate_limit_window_seconds
            ):
                entry.attempts = 0
                entry.window_started_at = now
            entries.append(entry)

        if any(
            entry.attempts >= self.settings.auth_login_rate_limit_max
            for entry in entries
        ):
            raise RateLimitExceededError(
                self.settings.auth_login_rate_limit_window_seconds
            )
        for entry in entries:
            entry.attempts += 1

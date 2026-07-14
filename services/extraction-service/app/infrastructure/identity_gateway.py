from dataclasses import dataclass

import httpx

from app.config import Settings
from app.errors import ForbiddenError, InvalidTokenError, UpstreamUnavailableError


@dataclass(frozen=True)
class Principal:
    id: str
    name: str | None
    email: str | None
    status: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    authorization: str

    def require_permission(self, permission: str) -> None:
        if permission not in self.permissions and "ADMIN" not in self.roles:
            raise ForbiddenError()


class IdentityGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def authenticate(self, authorization: str | None, correlation_id: str) -> Principal:
        if not authorization:
            raise InvalidTokenError()
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.identity_service_url,
                timeout=self.settings.identity_timeout_seconds,
            ) as client:
                response = await client.get(
                    "/auth/me",
                    headers={"Authorization": authorization, "X-Correlation-Id": correlation_id},
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("identity-service") from exc
        if response.status_code == 401:
            raise InvalidTokenError()
        if response.status_code >= 400:
            raise UpstreamUnavailableError("identity-service")
        payload = response.json()
        return Principal(
            id=payload.get("id") or payload.get("userId") or payload.get("sub") or "unknown",
            name=payload.get("name"),
            email=payload.get("email"),
            status=payload.get("status", "ACTIVE"),
            roles=tuple(payload.get("roles", [])),
            permissions=tuple(payload.get("permissions", [])),
            authorization=authorization,
        )

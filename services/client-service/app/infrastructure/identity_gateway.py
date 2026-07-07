from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.errors import ForbiddenError, InvalidTokenError, NotFoundError, UpstreamUnavailableError


@dataclass(frozen=True)
class Principal:
    id: str
    name: str
    email: str
    status: str
    roles: tuple[str, ...]
    permissions: tuple[str, ...]
    authorization: str

    @property
    def is_admin(self) -> bool:
        return "ADMIN" in self.roles


class IdentityGateway:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.identity_service_url
        self.timeout = settings.identity_timeout_seconds

    async def _get(
        self, path: str, authorization: str, correlation_id: str
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                response = await client.get(
                    path,
                    headers={
                        "Authorization": authorization,
                        "X-Correlation-Id": correlation_id,
                    },
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError() from exc
        if response.status_code == 401:
            raise InvalidTokenError()
        if response.status_code == 403:
            raise ForbiddenError()
        if response.status_code == 404:
            raise NotFoundError("User")
        if response.status_code >= 500:
            raise UpstreamUnavailableError()
        if response.status_code != 200:
            raise InvalidTokenError()
        return response.json()

    async def authenticate(
        self, authorization: str, correlation_id: str
    ) -> Principal:
        payload = await self._get("/auth/me", authorization, correlation_id)
        if payload.get("status") != "ACTIVE":
            raise InvalidTokenError()
        return Principal(
            id=payload["id"],
            name=payload["name"],
            email=payload["email"],
            status=payload["status"],
            roles=tuple(payload.get("roles", [])),
            permissions=tuple(payload.get("permissions", [])),
            authorization=authorization,
        )

    async def get_user(
        self, user_id: str, principal: Principal, correlation_id: str
    ) -> dict[str, Any]:
        return await self._get(
            f"/users/{user_id}", principal.authorization, correlation_id
        )


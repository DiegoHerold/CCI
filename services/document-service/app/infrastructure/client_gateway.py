from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.errors import ClientContextError, ForbiddenError, InvalidTokenError, UpstreamUnavailableError
from app.infrastructure.identity_gateway import Principal


@dataclass(frozen=True)
class ClientCompetenceContext:
    client_id: str
    competence_id: str
    period: str | None = None
    status: str | None = None


class ClientServiceHttpAdapter:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.client_service_url
        self.timeout = settings.client_service_timeout_seconds

    async def validate_competence(
        self,
        client_id: str,
        competence_id: str,
        principal: Principal,
        correlation_id: str,
    ) -> ClientCompetenceContext:
        path = f"/clients/{client_id}/competencies/{competence_id}"
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                response = await client.get(
                    path,
                    headers={
                        "Authorization": principal.authorization,
                        "X-Correlation-Id": correlation_id,
                    },
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("client-service") from exc
        if response.status_code == 401:
            raise InvalidTokenError()
        if response.status_code == 403:
            raise ForbiddenError("Client or competence access denied")
        if response.status_code == 404:
            raise ClientContextError(
                404,
                "CLIENT_COMPETENCE_NOT_FOUND",
                "Client or competence not found",
            )
        if response.status_code >= 500:
            raise UpstreamUnavailableError("client-service")
        if response.status_code != 200:
            raise ClientContextError(
                422,
                "CLIENT_COMPETENCE_INVALID",
                "Client competence could not be validated",
            )
        payload: dict[str, Any] = response.json()
        return ClientCompetenceContext(
            client_id=payload.get("clientId") or payload.get("client_id") or client_id,
            competence_id=payload.get("id") or competence_id,
            period=payload.get("period"),
            status=payload.get("status"),
        )

    async def validate_client(
        self,
        client_id: str,
        principal: Principal,
        correlation_id: str,
    ) -> None:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            ) as client:
                response = await client.get(
                    f"/clients/{client_id}",
                    headers={
                        "Authorization": principal.authorization,
                        "X-Correlation-Id": correlation_id,
                    },
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("client-service") from exc
        if response.status_code == 401:
            raise InvalidTokenError()
        if response.status_code == 403:
            raise ForbiddenError("Client access denied")
        if response.status_code == 404:
            raise ClientContextError(404, "CLIENT_NOT_FOUND", "Client not found")
        if response.status_code >= 500:
            raise UpstreamUnavailableError("client-service")
        if response.status_code != 200:
            raise ClientContextError(422, "CLIENT_INVALID", "Client could not be validated")

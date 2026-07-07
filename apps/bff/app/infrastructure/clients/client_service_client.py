from typing import Any

from app.infrastructure.clients.base_client import BaseInternalClient, InternalResponse


class ClientServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("client-service", base_url)

    async def call(
        self,
        method: str,
        path: str,
        correlation_id: str,
        authorization: str | None = None,
        payload: dict[str, Any] | None = None,
        params: list[tuple[str, str]] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        return await self.request(
            method,
            path,
            correlation_id,
            authorization=authorization,
            json=payload,
            params=params,
            client_ip=client_ip,
            user_agent=user_agent,
        )

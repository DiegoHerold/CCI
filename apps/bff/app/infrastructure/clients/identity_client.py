from typing import Any

from app.infrastructure.clients.base_client import BaseInternalClient, InternalResponse


class IdentityClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("identity-service", base_url)

    async def call(
        self,
        method: str,
        path: str,
        correlation_id: str,
        authorization: str | None = None,
        payload: dict[str, Any] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        return await self.request(
            method,
            path,
            correlation_id,
            authorization=authorization,
            json=payload,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def login(
        self,
        payload: dict[str, Any],
        correlation_id: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        return await self.call(
            "POST",
            "/auth/login",
            correlation_id,
            payload=payload,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def me(
        self,
        authorization: str | None,
        correlation_id: str,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        return await self.call(
            "GET",
            "/auth/me",
            correlation_id,
            authorization=authorization,
            client_ip=client_ip,
            user_agent=user_agent,
        )

    async def users(
        self,
        method: str,
        path: str,
        authorization: str | None,
        correlation_id: str,
        payload: dict[str, Any] | None = None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        return await self.call(
            method,
            path,
            correlation_id,
            authorization=authorization,
            payload=payload,
            client_ip=client_ip,
            user_agent=user_agent,
        )

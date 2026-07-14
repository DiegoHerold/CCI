from typing import Any

import httpx

from app.infrastructure.clients.base_client import BaseInternalClient, InternalResponse


class DocumentServiceClient(BaseInternalClient):
    def __init__(self, base_url: str) -> None:
        super().__init__("document-service", base_url)

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

    async def call_raw(
        self,
        method: str,
        path: str,
        correlation_id: str,
        *,
        authorization: str | None,
        body: bytes,
        content_type: str | None,
        client_ip: str | None = None,
        user_agent: str | None = None,
    ) -> InternalResponse:
        headers = self.request_headers(
            correlation_id,
            authorization=authorization,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        if content_type:
            headers["Content-Type"] = content_type
        async with httpx.AsyncClient(base_url=self.base_url, timeout=60.0) as client:
            response = await client.request(
                method,
                path,
                headers=headers,
                content=body,
            )
        try:
            payload: Any = response.json()
        except ValueError:
            payload = {
                "error": {
                    "code": "INVALID_UPSTREAM_RESPONSE",
                    "message": "Document Service returned a non-JSON response",
                }
            }
        return InternalResponse(
            status_code=response.status_code,
            payload=payload,
            www_authenticate=response.headers.get("WWW-Authenticate"),
        )

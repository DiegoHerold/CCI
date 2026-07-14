from typing import Any

import httpx

from app.config import Settings
from app.errors import UpstreamUnavailableError


class DocumentServicePort:
    async def get_document(
        self, document_id: str, *, authorization: str, correlation_id: str
    ) -> dict[str, Any] | None:
        raise NotImplementedError

    async def get_preview(
        self, document_id: str, *, authorization: str, correlation_id: str
    ) -> dict[str, Any] | None:
        raise NotImplementedError


class DocumentServiceHttpAdapter(DocumentServicePort):
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.document_service_url.rstrip("/")
        self.timeout = settings.document_service_timeout_seconds

    async def _get(self, path: str, *, authorization: str, correlation_id: str) -> dict[str, Any] | None:
        headers = {"Authorization": authorization, "X-Correlation-Id": correlation_id}
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.get(path, headers=headers)
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("document-service") from exc
        if response.status_code == 404:
            return None
        if response.status_code >= 500:
            raise UpstreamUnavailableError("document-service")
        response.raise_for_status()
        return response.json()

    async def get_document(
        self, document_id: str, *, authorization: str, correlation_id: str
    ) -> dict[str, Any] | None:
        return await self._get(f"/documents/{document_id}", authorization=authorization, correlation_id=correlation_id)

    async def get_preview(
        self, document_id: str, *, authorization: str, correlation_id: str
    ) -> dict[str, Any] | None:
        return await self._get(f"/documents/{document_id}/preview", authorization=authorization, correlation_id=correlation_id)

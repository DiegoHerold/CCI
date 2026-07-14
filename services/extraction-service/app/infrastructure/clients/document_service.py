from typing import Any

import httpx

from app.config import Settings
from app.errors import NotFoundError, UpstreamUnavailableError


class DocumentServiceHttpAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def _get(self, path: str, *, authorization: str, correlation_id: str) -> dict[str, Any] | None:
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.document_service_url,
                timeout=self.settings.document_service_timeout_seconds,
            ) as client:
                response = await client.get(
                    path,
                    headers={"Authorization": authorization, "X-Correlation-Id": correlation_id},
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("document-service") from exc
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise UpstreamUnavailableError("document-service")
        return response.json()

    async def get_document(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        document = await self._get(f"/documents/{document_id}", authorization=authorization, correlation_id=correlation_id)
        if document is None:
            raise NotFoundError("document")
        return document

    async def get_preview(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        preview = await self._get(f"/documents/{document_id}/preview", authorization=authorization, correlation_id=correlation_id)
        if preview is None:
            raise NotFoundError("document preview")
        return preview

    async def update_document_status(
        self,
        document_id: str,
        status: str,
        *,
        authorization: str,
        correlation_id: str,
        reason: str | None = None,
    ) -> None:
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.document_service_url,
                timeout=self.settings.document_service_timeout_seconds,
            ) as client:
                response = await client.patch(
                    f"/documents/{document_id}/status",
                    headers={"Authorization": authorization, "X-Correlation-Id": correlation_id},
                    json={"status": status, "reason": reason},
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("document-service") from exc
        if response.status_code == 404:
            raise NotFoundError("document")
        if response.status_code >= 400:
            raise UpstreamUnavailableError("document-service")

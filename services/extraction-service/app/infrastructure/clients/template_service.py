from typing import Any

import httpx

from app.config import Settings
from app.errors import NotFoundError, UpstreamUnavailableError


class TemplateServiceHttpAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def _get(self, path: str, *, authorization: str, correlation_id: str) -> dict[str, Any] | None:
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.template_service_url,
                timeout=self.settings.template_service_timeout_seconds,
            ) as client:
                response = await client.get(
                    path,
                    headers={"Authorization": authorization, "X-Correlation-Id": correlation_id},
                )
        except httpx.RequestError as exc:
            raise UpstreamUnavailableError("template-service") from exc
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise UpstreamUnavailableError("template-service")
        return response.json()

    async def get_latest_matching(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any] | None:
        return await self._get(
            f"/template-matching/documents/{document_id}",
            authorization=authorization,
            correlation_id=correlation_id,
        )

    async def get_matching_run(self, matching_run_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        run = await self._get(
            f"/template-matching/runs/{matching_run_id}",
            authorization=authorization,
            correlation_id=correlation_id,
        )
        if run is None:
            raise NotFoundError("template matching run")
        return run

    async def get_template(self, template_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        template = await self._get(f"/templates/{template_id}", authorization=authorization, correlation_id=correlation_id)
        if template is None:
            raise NotFoundError("template")
        return template

    async def get_template_version(
        self,
        template_id: str,
        template_version_id: str,
        *,
        authorization: str,
        correlation_id: str,
    ) -> dict[str, Any]:
        version = await self._get(
            f"/templates/{template_id}/versions/{template_version_id}",
            authorization=authorization,
            correlation_id=correlation_id,
        )
        if version is None:
            raise NotFoundError("template version")
        return version

    async def get_fields(self, template_id: str, *, authorization: str, correlation_id: str) -> list[dict[str, Any]]:
        payload = await self._get(f"/templates/{template_id}/fields", authorization=authorization, correlation_id=correlation_id)
        return [] if payload is None else list(payload.get("items", []))

    async def get_extraction_rules(
        self,
        template_id: str,
        *,
        authorization: str,
        correlation_id: str,
    ) -> list[dict[str, Any]]:
        payload = await self._get(
            f"/templates/{template_id}/extraction-rules",
            authorization=authorization,
            correlation_id=correlation_id,
        )
        return [] if payload is None else list(payload.get("items", []))

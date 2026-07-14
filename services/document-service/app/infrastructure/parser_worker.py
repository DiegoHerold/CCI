from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.config import Settings
from app.errors import BusinessRuleError


class ParserWorkerParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    client_id: str
    competence_id: str
    file_format: str
    original_filename: str
    storage_bucket: str
    storage_key: str
    preview_bucket: str
    preview_storage_key: str
    max_file_size_bytes: int
    max_preview_json_size_bytes: int


class ParserWorkerParseResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_id: str
    file_format: str
    parser_version: str
    storage_bucket: str
    storage_key: str
    page_count: int = 0
    sheet_count: int = 0
    text_block_count: int = 0
    table_count: int = 0
    requires_ocr: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParserWorkerClient:
    async def parse(self, request: ParserWorkerParseRequest) -> ParserWorkerParseResult:
        raise NotImplementedError


class HttpParserWorkerClient(ParserWorkerClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.parser_worker_url.rstrip("/")

    async def parse(self, request: ParserWorkerParseRequest) -> ParserWorkerParseResult:
        try:
            async with httpx.AsyncClient(timeout=self.settings.parser_worker_timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/parse",
                    json=request.model_dump(),
                    headers={"X-Correlation-Id": request.document_id},
                )
        except httpx.RequestError as exc:
            raise BusinessRuleError(
                "PARSER_WORKER_UNAVAILABLE",
                "Parser worker is unavailable",
                status_code=503,
            ) from exc

        if response.status_code >= 400:
            detail = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            message = detail.get("detail") if isinstance(detail, dict) else None
            raise BusinessRuleError(
                "DOCUMENT_PREVIEW_FAILED",
                str(message or "Parser worker failed to generate preview"),
                status_code=422,
            )
        return ParserWorkerParseResult.model_validate(response.json())

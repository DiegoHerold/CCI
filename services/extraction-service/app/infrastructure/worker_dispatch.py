from dataclasses import dataclass, field
from typing import Any

import httpx

from app.domain.enums import ExtractorWorkerType, SUPPORTED_WORKER_FORMATS
from app.errors import BusinessRuleError


@dataclass(frozen=True)
class WorkerSelection:
    worker_type: ExtractorWorkerType
    worker_name: str
    task_queue: str
    endpoint_url: str


@dataclass(frozen=True)
class WorkerDispatchResult:
    status: str
    raw_output: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class WorkerDispatcher:
    def __init__(
        self,
        pdf_task_queue: str,
        excel_task_queue: str,
        pdf_worker_url: str = "http://pdf-extractor-worker:8131",
        excel_worker_url: str = "http://excel-extractor-worker:8132",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.pdf_task_queue = pdf_task_queue
        self.excel_task_queue = excel_task_queue
        self.pdf_worker_url = pdf_worker_url.rstrip("/")
        self.excel_worker_url = excel_worker_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def choose_worker(self, file_format: str) -> WorkerSelection:
        normalized = file_format.upper()
        worker_type = SUPPORTED_WORKER_FORMATS.get(normalized)
        if worker_type is None:
            raise BusinessRuleError(
                "EXTRACTION_WORKER_UNSUPPORTED_FORMAT",
                f"No extractor worker is supported for {file_format}",
            )
        if worker_type == ExtractorWorkerType.PDF:
            return WorkerSelection(worker_type, worker_type.value, self.pdf_task_queue, self.pdf_worker_url)
        return WorkerSelection(worker_type, worker_type.value, self.excel_task_queue, self.excel_worker_url)

    async def dispatch(self, payload: dict[str, Any], selection: WorkerSelection) -> WorkerDispatchResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(f"{selection.endpoint_url}/extract", json=payload)
        except httpx.RequestError as exc:
            raise BusinessRuleError(
                "EXTRACTION_WORKER_UNAVAILABLE",
                f"{selection.worker_name} is unavailable: {exc}",
                status_code=503,
            ) from exc

        if response.status_code >= 400:
            raise BusinessRuleError(
                "EXTRACTION_WORKER_FAILED",
                f"{selection.worker_name} returned HTTP {response.status_code}: {response.text[:500]}",
                status_code=502,
            )

        data = response.json()
        return WorkerDispatchResult(
            status=str(data.get("status", "failed")),
            raw_output=data.get("raw_output") or {},
            warnings=list(data.get("warnings") or []),
            errors=list(data.get("errors") or []),
        )

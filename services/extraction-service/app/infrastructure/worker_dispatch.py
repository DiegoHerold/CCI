from dataclasses import dataclass, field
from typing import Any

from app.domain.enums import ExtractorWorkerType, SUPPORTED_WORKER_FORMATS
from app.errors import BusinessRuleError


@dataclass(frozen=True)
class WorkerSelection:
    worker_type: ExtractorWorkerType
    worker_name: str
    task_queue: str


@dataclass(frozen=True)
class WorkerDispatchResult:
    status: str
    raw_output: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class WorkerDispatcher:
    def __init__(self, pdf_task_queue: str, excel_task_queue: str) -> None:
        self.pdf_task_queue = pdf_task_queue
        self.excel_task_queue = excel_task_queue

    def choose_worker(self, file_format: str) -> WorkerSelection:
        normalized = file_format.upper()
        worker_type = SUPPORTED_WORKER_FORMATS.get(normalized)
        if worker_type is None:
            raise BusinessRuleError(
                "EXTRACTION_WORKER_UNSUPPORTED_FORMAT",
                f"No extractor worker is supported for {file_format}",
            )
        if worker_type == ExtractorWorkerType.PDF:
            return WorkerSelection(worker_type, worker_type.value, self.pdf_task_queue)
        return WorkerSelection(worker_type, worker_type.value, self.excel_task_queue)

    async def dispatch(self, payload: dict[str, Any], selection: WorkerSelection) -> WorkerDispatchResult:
        raise BusinessRuleError(
            "EXTRACTION_WORKER_UNAVAILABLE",
            f"{selection.worker_name} is not implemented yet. Fase 14 will provide the extractor worker.",
            status_code=503,
        )

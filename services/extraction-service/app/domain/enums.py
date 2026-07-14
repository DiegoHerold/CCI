from enum import StrEnum


class ExtractionJobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    STARTING = "starting"
    RUNNING = "running"
    WAITING_WORKER = "waiting_worker"
    WORKER_RUNNING = "worker_running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    REQUIRES_REVIEW = "requires_review"


class ExtractionAttemptStatus(StrEnum):
    STARTING = "starting"
    WORKER_RUNNING = "worker_running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionArtifactType(StrEnum):
    WORKER_RAW_OUTPUT = "worker_raw_output"
    WORKFLOW_LOG = "workflow_log"
    DEBUG_PAYLOAD = "debug_payload"


class ExtractorWorkerType(StrEnum):
    PDF = "pdf-extractor-worker"
    EXCEL = "excel-extractor-worker"
    OCR = "ocr-worker"
    UNSUPPORTED = "unsupported"


SUPPORTED_WORKER_FORMATS = {
    "PDF": ExtractorWorkerType.PDF,
    "XLS": ExtractorWorkerType.EXCEL,
    "XLSX": ExtractorWorkerType.EXCEL,
    "EXCEL": ExtractorWorkerType.EXCEL,
}


TERMINAL_STATUSES = {
    ExtractionJobStatus.COMPLETED,
    ExtractionJobStatus.FAILED,
    ExtractionJobStatus.CANCELLED,
}


ALLOWED_TRANSITIONS: dict[ExtractionJobStatus, set[ExtractionJobStatus]] = {
    ExtractionJobStatus.PENDING: {ExtractionJobStatus.QUEUED, ExtractionJobStatus.CANCELLED},
    ExtractionJobStatus.QUEUED: {ExtractionJobStatus.STARTING, ExtractionJobStatus.CANCELLED},
    ExtractionJobStatus.STARTING: {
        ExtractionJobStatus.RUNNING,
        ExtractionJobStatus.FAILED,
        ExtractionJobStatus.CANCELLED,
    },
    ExtractionJobStatus.RUNNING: {
        ExtractionJobStatus.WAITING_WORKER,
        ExtractionJobStatus.FAILED,
        ExtractionJobStatus.CANCELLED,
    },
    ExtractionJobStatus.WAITING_WORKER: {
        ExtractionJobStatus.WORKER_RUNNING,
        ExtractionJobStatus.FAILED,
        ExtractionJobStatus.CANCELLED,
    },
    ExtractionJobStatus.WORKER_RUNNING: {
        ExtractionJobStatus.COMPLETED,
        ExtractionJobStatus.FAILED,
        ExtractionJobStatus.REQUIRES_REVIEW,
        ExtractionJobStatus.CANCELLED,
    },
    ExtractionJobStatus.FAILED: {ExtractionJobStatus.RETRYING},
    ExtractionJobStatus.RETRYING: {ExtractionJobStatus.QUEUED, ExtractionJobStatus.CANCELLED},
    ExtractionJobStatus.REQUIRES_REVIEW: {
        ExtractionJobStatus.COMPLETED,
        ExtractionJobStatus.FAILED,
        ExtractionJobStatus.CANCELLED,
    },
    ExtractionJobStatus.COMPLETED: set(),
    ExtractionJobStatus.CANCELLED: set(),
}

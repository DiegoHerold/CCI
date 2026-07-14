from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExtractionJobStatus(str, Enum):
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


class ExtractionRequest(BaseModel):
    force_reprocess: bool = False
    matching_run_id: str | None = None
    template_id: str | None = None
    template_version_id: str | None = None


class ExtractionJob(BaseModel):
    extraction_job_id: str
    document_id: str
    client_id: str
    competence_id: str
    template_id: str
    template_version_id: str
    matching_run_id: str | None = None
    file_format: str
    status: ExtractionJobStatus
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(ge=1)
    workflow_id: str | None = None
    workflow_run_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ExtractionAttempt(BaseModel):
    attempt_id: str
    extraction_job_id: str
    attempt_number: int = Field(ge=1)
    status: str
    worker_type: str | None = None
    worker_name: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class ExtractionArtifact(BaseModel):
    artifact_id: str
    extraction_job_id: str
    document_id: str
    artifact_type: str
    storage_bucket: str
    storage_key: str
    content_hash: str | None = None


class ExtractionWorkflowInput(BaseModel):
    extraction_job_id: str
    document_id: str
    client_id: str
    competence_id: str
    template_id: str
    template_version_id: str
    file_format: str


class ExtractionWorkflowOutput(BaseModel):
    extraction_job_id: str
    status: ExtractionJobStatus
    artifact_id: str | None = None


class ExtractorWorkerInput(BaseModel):
    extraction_job_id: str
    document: dict[str, Any]
    preview: dict[str, Any]
    template: dict[str, Any]


class ExtractorWorkerOutput(BaseModel):
    extraction_job_id: str
    status: str
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ExtractionError(BaseModel):
    code: str
    message: str


class ExtractionRetryPolicy(BaseModel):
    max_attempts: int = Field(ge=1)
    initial_interval_seconds: int = Field(ge=1)
    backoff_coefficient: float = Field(ge=1)
    max_interval_seconds: int = Field(ge=1)


class ExtractedFieldValue(BaseModel):
    path: str
    raw_value: Any
    normalized_value: Any
    value_type: str
    confidence: float = Field(ge=0, le=1)
    evidence_ids: list[str] = Field(min_length=1)


class ExtractedObject(BaseModel):
    object_path: str
    fields: list[ExtractedFieldValue] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    job_id: str
    document_id: str
    client_id: str
    competence_id: str
    template_id: str
    template_version: int = Field(ge=1)
    status: str
    review_status: str = "not_required"
    objects: list[ExtractedObject] = Field(default_factory=list)
    error_code: str | None = None

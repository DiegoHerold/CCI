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


class ExtractionFieldStatus(str, Enum):
    EXTRACTED = "extracted"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"
    PARTIAL = "partial"


class ExtractionWorkerStatus(str, Enum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


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
    correlation_id: str | None = None
    document: dict[str, Any]
    preview: dict[str, Any]
    template: dict[str, Any]
    options: dict[str, Any] = Field(default_factory=dict)


class ExtractorWorkerOutput(BaseModel):
    extraction_job_id: str
    status: ExtractionWorkerStatus
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class ExtractionWarning(BaseModel):
    code: str
    message: str
    field_path: str | None = None
    rule_id: str | None = None


class ExtractionError(BaseModel):
    code: str
    message: str
    field_path: str | None = None
    rule_id: str | None = None


class RawExtractedField(BaseModel):
    field_id: str | None = None
    field_path: str
    raw_value: Any = None
    data_type: str | None = None
    confidence: float = Field(ge=0, le=1)
    status: ExtractionFieldStatus
    evidence: dict[str, Any] | None = None


class RawExtractedArrayItem(BaseModel):
    index: int = Field(ge=0)
    values: dict[str, Any] = Field(default_factory=dict)


class RawExtractedArray(BaseModel):
    field_path: str
    field_type: str = "array"
    items: list[RawExtractedArrayItem] = Field(default_factory=list)


class RawExtractedObject(BaseModel):
    field_path: str
    field_type: str
    value: dict[str, Any] | None = None
    items: list[RawExtractedArrayItem] | None = None


class ExtractionRuleExecutionResult(BaseModel):
    rule_id: str
    strategy: str
    field_path: str | None = None
    status: ExtractionFieldStatus
    confidence: float | None = Field(default=None, ge=0, le=1)
    warnings: list[ExtractionWarning] = Field(default_factory=list)
    errors: list[ExtractionError] = Field(default_factory=list)


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

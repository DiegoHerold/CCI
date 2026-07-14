from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExtractionArtifactType, ExtractionJobStatus
from app.infrastructure.database.models import ExtractionArtifact, ExtractionAttempt, ExtractionJob


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class ExtractionRequest(ApiModel):
    force_reprocess: bool = False
    matching_run_id: str | None = Field(default=None, max_length=36)
    template_id: str | None = Field(default=None, max_length=36)
    template_version_id: str | None = Field(default=None, max_length=36)


class ExtractionReprocessRequest(ApiModel):
    reason: str | None = Field(default=None, max_length=512)
    template_version_id: str | None = Field(default=None, max_length=36)


class ExtractionResponse(ApiModel):
    extraction_job_id: str
    document_id: str
    status: ExtractionJobStatus
    workflow_id: str | None = None
    template_id: str
    template_version_id: str

    @classmethod
    def from_entity(cls, job: ExtractionJob) -> "ExtractionResponse":
        return cls(
            extraction_job_id=job.id,
            document_id=job.document_id,
            status=ExtractionJobStatus(job.status),
            workflow_id=job.workflow_id,
            template_id=job.template_id,
            template_version_id=job.template_version_id,
        )


class ExtractionAttemptResponse(ApiModel):
    attempt_id: str
    attempt_number: int
    status: str
    worker_type: str | None = None
    worker_name: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None

    @classmethod
    def from_entity(cls, attempt: ExtractionAttempt) -> "ExtractionAttemptResponse":
        return cls(
            attempt_id=attempt.id,
            attempt_number=attempt.attempt_number,
            status=attempt.status,
            worker_type=attempt.worker_type,
            worker_name=attempt.worker_name,
            started_at=attempt.started_at,
            finished_at=attempt.finished_at,
            error_code=attempt.error_code,
            error_message=attempt.error_message,
        )


class ExtractionArtifactResponse(ApiModel):
    artifact_id: str
    artifact_type: ExtractionArtifactType
    storage_bucket: str
    storage_key: str
    content_hash: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, artifact: ExtractionArtifact) -> "ExtractionArtifactResponse":
        return cls(
            artifact_id=artifact.id,
            artifact_type=ExtractionArtifactType(artifact.artifact_type),
            storage_bucket=artifact.storage_bucket,
            storage_key=artifact.storage_key,
            content_hash=artifact.content_hash,
            created_at=artifact.created_at,
        )


class ExtractionJobResponse(ApiModel):
    extraction_job_id: str
    document_id: str
    client_id: str
    competence_id: str
    template_id: str
    template_version_id: str
    matching_run_id: str | None = None
    file_format: str
    status: ExtractionJobStatus
    attempt_count: int
    max_attempts: int
    workflow_id: str | None = None
    workflow_run_id: str | None = None
    requested_by: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_code: str | None = None
    error_message: str | None = None
    attempts: list[ExtractionAttemptResponse] = Field(default_factory=list)
    artifacts: list[ExtractionArtifactResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, job: ExtractionJob) -> "ExtractionJobResponse":
        return cls(
            extraction_job_id=job.id,
            document_id=job.document_id,
            client_id=job.client_id,
            competence_id=job.competence_id,
            template_id=job.template_id,
            template_version_id=job.template_version_id,
            matching_run_id=job.matching_run_id,
            file_format=job.file_format,
            status=ExtractionJobStatus(job.status),
            attempt_count=job.attempt_count,
            max_attempts=job.max_attempts,
            workflow_id=job.workflow_id,
            workflow_run_id=job.workflow_run_id,
            requested_by=job.requested_by,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_code=job.error_code,
            error_message=job.error_message,
            attempts=[ExtractionAttemptResponse.from_entity(item) for item in job.attempts],
            artifacts=[ExtractionArtifactResponse.from_entity(item) for item in job.artifacts],
            created_at=job.created_at,
            updated_at=job.updated_at,
        )


class ExtractionJobListResponse(ApiModel):
    items: list[ExtractionJobResponse]


class ExtractionStatusResponse(ApiModel):
    extraction_job_id: str
    status: ExtractionJobStatus
    attempt_count: int
    error_message: str | None = None

    @classmethod
    def from_entity(cls, job: ExtractionJob) -> "ExtractionStatusResponse":
        return cls(
            extraction_job_id=job.id,
            status=ExtractionJobStatus(job.status),
            attempt_count=job.attempt_count,
            error_message=job.error_message,
        )


class WorkerDocumentPayload(ApiModel):
    document_id: str
    file_format: str
    storage_bucket: str | None = None
    storage_key: str | None = None


class WorkerPreviewPayload(ApiModel):
    preview_id: str | None = None
    storage_bucket: str | None = None
    storage_key: str | None = None
    preview: dict[str, Any] | None = None


class WorkerTemplatePayload(ApiModel):
    template_id: str
    template_version_id: str
    file_format: str
    fields: list[dict[str, Any]]
    extraction_rules: list[dict[str, Any]]


class ExtractorWorkerInput(ApiModel):
    extraction_job_id: str
    document: WorkerDocumentPayload
    preview: WorkerPreviewPayload
    template: WorkerTemplatePayload


class ExtractorWorkerOutput(ApiModel):
    extraction_job_id: str
    status: str
    raw_output: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

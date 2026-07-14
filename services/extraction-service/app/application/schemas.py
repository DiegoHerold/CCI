from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExtractionArtifactType, ExtractionJobStatus
from app.infrastructure.database.models import ExtractionArtifact, ExtractionAttempt, ExtractionJob
from app.infrastructure.database.models import (
    ExtractedArrayItem,
    ExtractedFieldValue,
    ExtractedObject,
    ExtractionEvidence,
    ExtractionResult,
)


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


class NormalizationReprocessRequest(ApiModel):
    reason: str | None = Field(default=None, max_length=512)


class FieldCorrectionRequest(ApiModel):
    raw_value: Any
    reason: str | None = Field(default=None, max_length=512)


class FieldReviewRequest(ApiModel):
    reason: str | None = Field(default=None, max_length=512)


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


class ExtractionResultSummaryResponse(ApiModel):
    extraction_result_id: str
    extraction_job_id: str
    document_id: str
    client_id: str
    competence_id: str
    template_id: str
    template_version_id: str
    status: str
    field_count: int
    normalized_count: int
    requires_review_count: int
    error_count: int
    warning_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, result: ExtractionResult) -> "ExtractionResultSummaryResponse":
        return cls(
            extraction_result_id=result.id,
            extraction_job_id=result.extraction_job_id,
            document_id=result.document_id,
            client_id=result.client_id,
            competence_id=result.competence_id,
            template_id=result.template_id,
            template_version_id=result.template_version_id,
            status=result.status,
            field_count=result.field_count,
            normalized_count=result.normalized_count,
            requires_review_count=result.requires_review_count,
            error_count=result.error_count,
            warning_count=result.warning_count,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class ExtractedFieldValueResponse(ApiModel):
    field_value_id: str
    extraction_result_id: str
    field_id: str | None = None
    field_path: str
    field_type: str
    raw_value: Any = None
    normalized_value: str | None = None
    display_value: str | None = None
    normalized_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None
    confidence: float
    status: str
    evidence_id: str | None = None
    is_required: bool
    item_index: int | None = None

    @classmethod
    def from_entity(cls, field: ExtractedFieldValue) -> "ExtractedFieldValueResponse":
        return cls(
            field_value_id=field.id,
            extraction_result_id=field.extraction_result_id,
            field_id=field.field_id,
            field_path=field.field_path,
            field_type=field.field_type,
            raw_value=field.raw_value,
            normalized_value=field.normalized_value,
            display_value=field.display_value,
            normalized_json=field.normalized_json,
            metadata_json=field.metadata_json,
            confidence=field.confidence,
            status=field.status,
            evidence_id=field.evidence_id,
            is_required=field.is_required,
            item_index=field.item_index,
        )


class ExtractedFieldListResponse(ApiModel):
    items: list[ExtractedFieldValueResponse]


class ExtractedObjectResponse(ApiModel):
    object_id: str
    extraction_result_id: str
    parent_object_id: str | None = None
    field_path: str
    field_type: str
    object_type: str | None = None
    item_index: int | None = None
    status: str

    @classmethod
    def from_entity(cls, obj: ExtractedObject) -> "ExtractedObjectResponse":
        return cls(
            object_id=obj.id,
            extraction_result_id=obj.extraction_result_id,
            parent_object_id=obj.parent_object_id,
            field_path=obj.field_path,
            field_type=obj.field_type,
            object_type=obj.object_type,
            item_index=obj.item_index,
            status=obj.status,
        )


class ExtractedObjectListResponse(ApiModel):
    items: list[ExtractedObjectResponse]


class ExtractedArrayItemResponse(ApiModel):
    array_item_id: str
    extraction_result_id: str
    array_field_path: str
    item_index: int
    status: str
    confidence: float

    @classmethod
    def from_entity(cls, item: ExtractedArrayItem) -> "ExtractedArrayItemResponse":
        return cls(
            array_item_id=item.id,
            extraction_result_id=item.extraction_result_id,
            array_field_path=item.array_field_path,
            item_index=item.item_index,
            status=item.status,
            confidence=item.confidence,
        )


class ExtractedArrayItemListResponse(ApiModel):
    items: list[ExtractedArrayItemResponse]


class ExtractionEvidenceResponse(ApiModel):
    evidence_id: str
    extraction_result_id: str
    document_id: str
    field_value_id: str | None = None
    evidence_type: str
    page_number: int | None = None
    bbox_json: dict[str, Any] | None = None
    sheet_name: str | None = None
    cell_range: str | None = None
    source_text: str | None = None
    source_value: Any = None
    rule_id: str | None = None
    rule_strategy: str | None = None
    template_id: str
    template_version_id: str
    confidence: float | None = None

    @classmethod
    def from_entity(cls, evidence: ExtractionEvidence) -> "ExtractionEvidenceResponse":
        return cls(
            evidence_id=evidence.id,
            extraction_result_id=evidence.extraction_result_id,
            document_id=evidence.document_id,
            field_value_id=evidence.field_value_id,
            evidence_type=evidence.evidence_type,
            page_number=evidence.page_number,
            bbox_json=evidence.bbox_json,
            sheet_name=evidence.sheet_name,
            cell_range=evidence.cell_range,
            source_text=evidence.source_text,
            source_value=evidence.source_value,
            rule_id=evidence.rule_id,
            rule_strategy=evidence.rule_strategy,
            template_id=evidence.template_id,
            template_version_id=evidence.template_version_id,
            confidence=evidence.confidence,
        )


class ExtractionEvidenceListResponse(ApiModel):
    items: list[ExtractionEvidenceResponse]

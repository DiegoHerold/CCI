from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    DOCUMENT_UPLOADED = "DocumentUploaded"
    DOCUMENT_DUPLICATE_DETECTED = "DocumentDuplicateDetected"
    DOCUMENT_REJECTED = "DocumentRejected"
    DOCUMENT_STORAGE_FAILED = "DocumentStorageFailed"
    DOCUMENT_PREVIEW_REQUESTED = "DocumentPreviewRequested"
    DOCUMENT_PREVIEW_STARTED = "DocumentPreviewStarted"
    DOCUMENT_PREVIEW_GENERATED = "DocumentPreviewGenerated"
    DOCUMENT_PREVIEW_FAILED = "DocumentPreviewFailed"
    TEMPLATE_CATEGORY_CREATED = "TemplateCategoryCreated"
    TEMPLATE_CREATED = "TemplateCreated"
    TEMPLATE_UPDATED = "TemplateUpdated"
    TEMPLATE_FIELD_CREATED = "TemplateFieldCreated"
    TEMPLATE_IDENTIFICATION_SIGNAL_CREATED = "TemplateIdentificationSignalCreated"
    TEMPLATE_ANNOTATION_CREATED = "TemplateAnnotationCreated"
    TEMPLATE_ANNOTATION_UPDATED = "TemplateAnnotationUpdated"
    TEMPLATE_EXTRACTION_RULE_CREATED = "TemplateExtractionRuleCreated"
    TEMPLATE_VERSION_CREATED = "TemplateVersionCreated"
    TEMPLATE_VERSION_PUBLISHED = "TemplateVersionPublished"
    TEMPLATE_ARCHIVED = "TemplateArchived"
    TEMPLATE_MATCHED = "TemplateMatched"
    TEMPLATE_NOT_FOUND = "TemplateNotFound"
    TEMPLATE_AMBIGUOUS = "TemplateAmbiguous"
    TEMPLATE_MANUALLY_CONFIRMED = "TemplateManuallyConfirmed"
    EXTRACTION_REQUESTED = "ExtractionRequested"
    EXTRACTION_STARTED = "ExtractionStarted"
    EXTRACTION_WORKER_DISPATCHED = "ExtractionWorkerDispatched"
    EXTRACTION_COMPLETED = "ExtractionCompleted"
    EXTRACTION_FAILED = "ExtractionFailed"
    EXTRACTION_RETRY_SCHEDULED = "ExtractionRetryScheduled"
    EXTRACTION_CANCELLED = "ExtractionCancelled"
    EXTRACTION_REVIEWED = "ExtractionReviewed"
    EXTRACTION_NORMALIZATION_STARTED = "ExtractionNormalizationStarted"
    EXTRACTION_NORMALIZATION_COMPLETED = "ExtractionNormalizationCompleted"
    EXTRACTION_NORMALIZATION_FAILED = "ExtractionNormalizationFailed"
    EXTRACTION_RESULTS_SAVED = "ExtractionResultsSaved"
    EXTRACTION_REQUIRES_REVIEW = "ExtractionRequiresReview"
    EXTRACTION_FIELD_CORRECTED = "ExtractionFieldCorrected"
    EXTRACTION_FIELD_APPROVED = "ExtractionFieldApproved"
    EXTRACTION_FIELD_REJECTED = "ExtractionFieldRejected"
    EXTRACTION_RESULT_APPROVED = "ExtractionResultApproved"
    RULE_PUBLISHED = "RulePublished"
    RULE_EXECUTION_COMPLETED = "RuleExecutionCompleted"
    CONFERENCE_STARTED = "ConferenceStarted"
    CONFERENCE_COMPLETED = "ConferenceCompleted"
    REPORT_REQUESTED = "ReportRequested"
    REPORT_GENERATED = "ReportGenerated"
    FILE_IMPORTED = "file.imported"
    DOCUMENT_CLASSIFIED = "document.classified"
    DOCUMENT_AMBIGUOUS = "document.ambiguous"
    DOCUMENT_MISSING = "document.missing"
    DOCUMENT_CONFIRMED = "document.confirmed"
    EXTRACTION_STARTED = "extraction.started"
    RAW_EXTRACTED = "raw.extracted"
    VARIABLES_NORMALIZED = "variables.normalized"
    VARIABLES_READY = "variables.ready"
    VARIABLES_NEED_REVIEW = "variables.need_review"
    SCHEDULE_DUE = "schedule.due"
    FOLDER_READY = "folder.ready"
    EXECUTION_STARTED = "execution.started"
    RULE_EXECUTED = "rule.executed"
    RESULT_CREATED = "result.created"
    DIVERGENCE_FOUND = "divergence.found"
    EXECUTION_FINISHED = "execution.finished"
    AUDIT_CREATED = "audit.created"
    REPORT_GENERATED = "report.generated"
    LOG_CREATED = "log.created"


class EventEnvelope(BaseModel):
    event_id: str
    event_type: EventType
    version: int = Field(default=1, ge=1)
    occurred_at: datetime
    correlation_id: str
    causation_id: str | None = None
    producer: str
    client_id: str | None = None
    competence_id: str | None = None
    execution_id: str | None = None
    document_id: str | None = None
    payload: dict[str, Any]

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
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

from typing import Any

from pydantic import BaseModel, Field


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

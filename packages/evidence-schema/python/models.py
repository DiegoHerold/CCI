from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class PdfEvidence(BaseModel):
    kind: Literal["pdf"] = "pdf"
    page: int = Field(ge=1)
    bbox: BoundingBox | None = None


class ExcelEvidence(BaseModel):
    kind: Literal["excel"] = "excel"
    sheet: str
    cell_range: str


class Evidence(BaseModel):
    evidence_id: str
    document_id: str
    template_id: str | None = None
    template_version: int | None = Field(default=None, ge=1)
    rule_id: str | None = None
    source_text: str | None = None
    confidence: float = Field(ge=0, le=1)
    source: PdfEvidence | ExcelEvidence


class SourceReference(BaseModel):
    document_id: str
    preview_id: str | None = None
    storage_bucket: str | None = None
    storage_key: str | None = None
    page: int | None = Field(default=None, ge=1)
    sheet: str | None = None
    cell_range: str | None = None
    bbox: BoundingBox | None = None


class TemplateRuleReference(BaseModel):
    template_id: str
    template_version_id: str
    field_id: str | None = None
    extraction_rule_id: str | None = None


class RawExtractionEvidence(BaseModel):
    evidence_id: str
    extraction_job_id: str
    source: SourceReference
    template_rule: TemplateRuleReference | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw_text: str | None = None

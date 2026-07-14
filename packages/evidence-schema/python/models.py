from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class PdfBoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


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


class ExtractionEvidenceConfidence(BaseModel):
    confidence: float = Field(ge=0, le=1)
    factors: list[str] = Field(default_factory=list)


class PdfExtractionEvidence(BaseModel):
    evidence_type: Literal["pdf"] = "pdf"
    document_id: str
    page_number: int = Field(ge=1)
    bbox: PdfBoundingBox | None = None
    source_text: str | None = None
    rule_id: str | None = None
    rule_strategy: str | None = None
    confidence: float = Field(ge=0, le=1)


class CellRange(BaseModel):
    sheet_name: str
    cell_range: str


class ExcelExtractionEvidence(BaseModel):
    evidence_type: Literal["excel"] = "excel"
    document_id: str
    sheet_name: str
    cell_range: str | None = None
    source_value: str | int | float | bool | None = None
    rule_id: str | None = None
    rule_strategy: str | None = None
    confidence: float = Field(ge=0, le=1)


class RawExtractionEvidence(BaseModel):
    evidence_id: str
    extraction_job_id: str
    source: SourceReference
    template_rule: TemplateRuleReference | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    raw_text: str | None = None

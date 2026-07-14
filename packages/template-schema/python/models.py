from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TemplateStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class TemplateVersionStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TemplateMatchingStatus(str, Enum):
    MATCHED = "matched"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    FAILED = "failed"


class TemplateFileFormat(str, Enum):
    PDF = "PDF"
    XLSX = "XLSX"
    XLS = "XLS"
    CSV = "CSV"
    TXT = "TXT"
    DOCX = "DOCX"
    XML = "XML"
    IMAGE = "IMAGE"


TemplateFormat = TemplateFileFormat


class TemplateStructureType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    HIERARCHICAL = "hierarchical"
    FORM = "form"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class IdentificationSignalType(str, Enum):
    CONTAINS_TEXT = "contains_text"
    CONTAINS_ANY_TEXT = "contains_any_text"
    CONTAINS_ALL_TEXT = "contains_all_text"
    NOT_CONTAINS_TEXT = "not_contains_text"
    REGEX = "regex"
    FILE_FORMAT = "file_format"
    SHEET_NAME = "sheet_name"
    COLUMN_HEADER = "column_header"
    TABLE_HEADER = "table_header"
    PAGE_COUNT_RANGE = "page_count_range"
    HAS_CNPJ = "has_cnpj"
    HAS_DATE = "has_date"
    HAS_CURRENCY_VALUES = "has_currency_values"
    STRUCTURE_HINT = "structure_hint"


class ExtractionStrategy(str, Enum):
    FIND_NEAR_LABEL = "find_near_label"
    FIXED_BBOX = "fixed_bbox"
    PDF_AREA_TABLE = "pdf_area_table"
    PDF_COLUMN_BY_X_POSITION = "pdf_column_by_x_position"
    HIERARCHICAL_LINES = "hierarchical_lines"
    EXCEL_CELL_ADDRESS = "excel_cell_address"
    EXCEL_COLUMN_BY_HEADER = "excel_column_by_header"
    EXCEL_RANGE_TABLE = "excel_range_table"
    EXCEL_SHEET_BY_NAME = "excel_sheet_by_name"
    REGEX_FROM_TEXT = "regex_from_text"


class TemplateCategory(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    status: str = "active"


class IdentificationSignal(BaseModel):
    id: str | None = None
    template_id: str | None = None
    signal_type: IdentificationSignalType
    weight: float = Field(default=1, ge=0, le=100)
    value: str
    required: bool = False
    negative: bool = False


class Template(BaseModel):
    template_id: str
    name: str
    description: str | None = None
    category_id: str
    file_format: TemplateFileFormat
    structure_type: TemplateStructureType
    status: TemplateStatus
    active_version_id: str | None = None


class TemplateVersion(BaseModel):
    id: str
    template_id: str
    version_number: int = Field(ge=1)
    status: TemplateVersionStatus
    snapshot: dict[str, Any] = Field(default_factory=dict)


class ExtractionRule(BaseModel):
    id: str | None = None
    template_id: str | None = None
    template_version_id: str | None = None
    field_id: str
    rule_type: str | None = None
    strategy: ExtractionStrategy
    config: dict[str, Any] = Field(default_factory=dict)
    confidence_hint: float | None = Field(default=None, ge=0, le=1)
    created_from_annotation_id: str | None = None


class TemplateSummary(Template):
    field_count: int = 0
    extraction_rule_count: int = 0


class TemplateDetail(Template):
    identification_signals: list[IdentificationSignal] = Field(default_factory=list)
    versions: list[TemplateVersion] = Field(default_factory=list)


class TemplateBuilderState(BaseModel):
    template: TemplateDetail
    active_version: TemplateVersion | None = None
    draft_version: TemplateVersion | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    extraction_rules: list[ExtractionRule] = Field(default_factory=list)
    identification_signals: list[IdentificationSignal] = Field(default_factory=list)


class TemplateBuilderSaveRequest(BaseModel):
    fields: list[dict[str, Any]] = Field(default_factory=list)
    annotations: list[dict[str, Any]] = Field(default_factory=list)
    extraction_rules: list[ExtractionRule] = Field(default_factory=list)


class DocumentProfile(BaseModel):
    document_id: str
    client_id: str | None = None
    competence_id: str | None = None
    file_format: TemplateFileFormat
    mime_type: str | None = None
    original_filename: str | None = None
    page_count: int = Field(default=0, ge=0)
    sheet_count: int = Field(default=0, ge=0)
    requires_ocr: bool = False
    text_sample: str = ""
    normalized_text_sample: str = ""
    detected_keywords: list[str] = Field(default_factory=list)
    detected_regex_patterns: list[str] = Field(default_factory=list)
    has_cnpj: bool = False
    has_dates: bool = False
    has_currency_values: bool = False
    has_tables: bool = False
    structure_hints: list[str] = Field(default_factory=list)
    sheet_names: list[str] = Field(default_factory=list)
    detected_headers: list[str] = Field(default_factory=list)


class TemplateMatchingRequest(BaseModel):
    force_reprocess: bool = False
    category_hint: str | None = None
    max_candidates: int | None = Field(default=None, ge=1, le=100)


class TemplateMatchingCandidate(BaseModel):
    template_id: str
    template_version_id: str | None = None
    category_id: str | None = None
    template_name: str | None = None
    category_name: str | None = None
    score: float = Field(ge=0, le=1)
    rank_position: int = Field(ge=1)
    matched_signals: list[str] = Field(default_factory=list)
    missing_required_signals: list[str] = Field(default_factory=list)
    negative_matches: list[str] = Field(default_factory=list)
    score_details: dict[str, Any] = Field(default_factory=dict)


class TemplateMatchingResult(BaseModel):
    matching_run_id: str
    document_id: str
    status: TemplateMatchingStatus
    matched_template_id: str | None = None
    matched_template_version_id: str | None = None
    matched_category_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    decision_reason: str
    manual_override: bool = False
    candidates: list[TemplateMatchingCandidate] = Field(default_factory=list)


TemplateMatchingRun = TemplateMatchingResult

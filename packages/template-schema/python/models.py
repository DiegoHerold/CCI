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


class TemplateSummary(Template):
    field_count: int = 0
    extraction_rule_count: int = 0


class TemplateDetail(Template):
    identification_signals: list[IdentificationSignal] = Field(default_factory=list)
    versions: list[TemplateVersion] = Field(default_factory=list)

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnnotationType(str, Enum):
    PDF_TEXT_BLOCK = "pdf_text_block"
    PDF_LINE = "pdf_line"
    PDF_TOKEN = "pdf_token"
    PDF_AREA = "pdf_area"
    PDF_TABLE_CANDIDATE = "pdf_table_candidate"
    EXCEL_CELL = "excel_cell"
    EXCEL_COLUMN = "excel_column"
    EXCEL_ROW = "excel_row"
    EXCEL_RANGE = "excel_range"
    EXCEL_TABLE_CANDIDATE = "excel_table_candidate"


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class AnnotationTargetField(BaseModel):
    field_id: str
    field_path: str


class PdfTextBlockAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.PDF_TEXT_BLOCK
    document_id: str | None = None
    page_number: int = Field(ge=1)
    text: str | None = None
    bbox: BoundingBox
    source: str = "preview"


class PdfAreaAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.PDF_AREA
    document_id: str | None = None
    page_number: int = Field(ge=1)
    bbox: BoundingBox
    source: str = "preview"


class PdfTableCandidateAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.PDF_TABLE_CANDIDATE
    document_id: str | None = None
    page_number: int = Field(ge=1)
    table_id: str | None = None
    bbox: BoundingBox | None = None


class ExcelCellAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.EXCEL_CELL
    document_id: str | None = None
    sheet_name: str
    sheet_index: int = Field(ge=0)
    row: int = Field(ge=1)
    column: int = Field(ge=1)
    address: str


class ExcelColumnAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.EXCEL_COLUMN
    document_id: str | None = None
    sheet_name: str
    sheet_index: int = Field(ge=0)
    column: int = Field(ge=1)
    column_letter: str
    header: str | None = None


class ExcelRangeAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.EXCEL_RANGE
    document_id: str | None = None
    sheet_name: str
    sheet_index: int = Field(ge=0)
    start_row: int = Field(ge=1)
    start_column: int = Field(ge=1)
    end_row: int = Field(ge=1)
    end_column: int = Field(ge=1)


class ExcelTableCandidateAnnotation(BaseModel):
    selection_type: AnnotationType = AnnotationType.EXCEL_TABLE_CANDIDATE
    document_id: str | None = None
    sheet_name: str
    sheet_index: int = Field(ge=0)
    table_id: str | None = None


class TemplateAnnotation(BaseModel):
    id: str
    template_id: str
    template_version_id: str | None = None
    document_id: str
    field_id: str
    annotation_type: AnnotationType
    source_preview_id: str | None = None
    selected_text: str | None = None
    selection_payload: dict[str, Any]


Annotation = TemplateAnnotation


class CreateAnnotationRequest(BaseModel):
    template_version_id: str | None = None
    field_id: str
    document_id: str
    annotation_type: AnnotationType
    source_preview_id: str | None = None
    selected_text: str | None = None
    selection_payload: dict[str, Any]


class CreateAnnotationResponse(BaseModel):
    annotation: TemplateAnnotation


class CreateAnnotationWithRuleRequest(CreateAnnotationRequest):
    generate_rule: bool = True
    rule_strategy: str | None = None
    rule_config: dict[str, Any] | None = None

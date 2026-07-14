from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    BALANCETE = "balancete"
    GUIA_INSS = "guia_inss"
    GUIA_FGTS = "guia_fgts"
    FOLHA_PAGAMENTO = "folha_pagamento"
    RELATORIO_FISCAL = "relatorio_fiscal"
    RELATORIO_CONTABIL = "relatorio_contabil"
    EXTRATO = "extrato"
    OUTRO = "outro"
    DESCONHECIDO = "desconhecido"


class DocumentStatus(str, Enum):
    IMPORTED = "imported"
    CLASSIFIED = "classified"
    TEMPLATE_MATCHED = "template_matched"
    TEMPLATE_NOT_FOUND = "template_not_found"
    TEMPLATE_AMBIGUOUS = "template_ambiguous"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXTRACTION_PENDING = "extraction_pending"
    EXTRACTION_RUNNING = "extraction_running"
    EXTRACTED = "extracted"
    REVIEW_PENDING = "review_pending"
    EXTRACTION_FAILED = "extraction_failed"
    ERROR = "error"


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class Evidence(BaseModel):
    document_id: str
    page: int | None = Field(default=None, ge=1)
    row: int | None = Field(default=None, ge=1)
    column: str | None = None
    cell: str | None = None
    text: str | None = None
    bounding_box: BoundingBox | None = None


class PreviewBoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float


class PdfToken(BaseModel):
    token_id: str
    text: str
    bbox: PreviewBoundingBox
    confidence: float | None = Field(default=None, ge=0, le=1)


class PdfLine(BaseModel):
    line_id: str
    text: str
    bbox: PreviewBoundingBox
    tokens: list[PdfToken] = Field(default_factory=list)


class PdfTextBlock(BaseModel):
    block_id: str
    text: str
    bbox: PreviewBoundingBox
    confidence: float | None = Field(default=None, ge=0, le=1)
    source: str


class PdfTableCandidate(BaseModel):
    table_id: str
    bbox: PreviewBoundingBox
    rows: list[Any] = Field(default_factory=list)
    columns: list[Any] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class PdfPagePreview(BaseModel):
    page_number: int = Field(ge=1)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    rotation: int
    text_blocks: list[PdfTextBlock] = Field(default_factory=list)
    lines: list[PdfLine] = Field(default_factory=list)
    tables: list[PdfTableCandidate] = Field(default_factory=list)


class ExcelCellPreview(BaseModel):
    cell_id: str
    address: str
    row: int = Field(ge=1)
    column: int = Field(ge=1)
    column_letter: str
    value: Any | None = None
    raw_value: Any | None = None
    data_type: str
    is_merged: bool = False
    merged_range: str | None = None


class ExcelMergedRange(BaseModel):
    range: str
    start_row: int = Field(ge=1)
    start_column: int = Field(ge=1)
    end_row: int = Field(ge=1)
    end_column: int = Field(ge=1)


class ExcelDetectedHeader(BaseModel):
    row: int = Field(ge=1)
    values: list[str]
    confidence: float = Field(ge=0, le=1)


class ExcelTableCandidate(BaseModel):
    table_id: str
    range: str
    header_row: int = Field(ge=1)
    start_row: int = Field(ge=1)
    end_row: int = Field(ge=1)
    confidence: float = Field(ge=0, le=1)


class ExcelSheetPreview(BaseModel):
    sheet_id: str
    name: str
    index: int = Field(ge=0)
    max_row: int = Field(ge=0)
    max_column: int = Field(ge=0)
    cells: list[ExcelCellPreview] = Field(default_factory=list)
    merged_cells: list[ExcelMergedRange] = Field(default_factory=list)
    detected_headers: list[ExcelDetectedHeader] = Field(default_factory=list)
    detected_tables: list[ExcelTableCandidate] = Field(default_factory=list)


class PreviewSummary(BaseModel):
    page_count: int = Field(ge=0)
    sheet_count: int = Field(ge=0)
    text_block_count: int = Field(ge=0)
    table_count: int = Field(ge=0)


class PdfDocumentPreview(BaseModel):
    document_id: str
    file_format: str = "PDF"
    parser_version: str
    generated_at: datetime
    requires_ocr: bool
    ocr_reason: str | None = None
    pages: list[PdfPagePreview]
    summary: PreviewSummary


class ExcelDocumentPreview(BaseModel):
    document_id: str
    file_format: str
    parser_version: str
    generated_at: datetime
    requires_ocr: bool = False
    sheets: list[ExcelSheetPreview]
    summary: PreviewSummary


ParsedDocumentPreview = PdfDocumentPreview | ExcelDocumentPreview


class PdfTextSelection(BaseModel):
    selection_type: str
    document_id: str
    page_number: int = Field(ge=1)
    text: str
    bbox: PreviewBoundingBox
    source: str = "preview"


class PdfAreaSelection(BaseModel):
    selection_type: str = "pdf_area"
    document_id: str
    page_number: int = Field(ge=1)
    bbox: PreviewBoundingBox
    source: str = "user_area_selection"


class PdfTableSelection(BaseModel):
    selection_type: str = "pdf_table_candidate"
    document_id: str
    page_number: int = Field(ge=1)
    table_id: str
    bbox: PreviewBoundingBox
    confidence: float = Field(ge=0, le=1)
    source: str = "preview"


class ExcelCellSelection(BaseModel):
    selection_type: str = "excel_cell"
    document_id: str
    sheet_name: str
    sheet_index: int = Field(ge=0)
    cell: dict[str, Any]
    source: str = "preview"


class ExcelColumnSelection(BaseModel):
    selection_type: str = "excel_column"
    document_id: str
    sheet_name: str
    sheet_index: int = Field(ge=0)
    column: int = Field(ge=1)
    column_letter: str
    header: str | None = None
    source: str = "user_column_selection"


class ExcelRowSelection(BaseModel):
    selection_type: str = "excel_row"
    document_id: str
    sheet_name: str
    sheet_index: int = Field(ge=0)
    row: int = Field(ge=1)
    source: str = "user_row_selection"


class ExcelRangeSelection(BaseModel):
    selection_type: str = "excel_range"
    document_id: str
    sheet_name: str
    sheet_index: int = Field(ge=0)
    range: dict[str, Any]
    source: str = "user_range_selection"


class ExcelTableSelection(BaseModel):
    selection_type: str = "excel_table_candidate"
    document_id: str
    sheet_name: str
    sheet_index: int = Field(ge=0)
    table_id: str
    range: str
    header_row: int = Field(ge=1)
    start_row: int = Field(ge=1)
    end_row: int = Field(ge=1)
    confidence: float = Field(ge=0, le=1)
    source: str = "preview"


DocumentSelection = (
    PdfTextSelection
    | PdfAreaSelection
    | PdfTableSelection
    | ExcelCellSelection
    | ExcelColumnSelection
    | ExcelRowSelection
    | ExcelRangeSelection
    | ExcelTableSelection
)


class PdfEvidenceHighlight(BaseModel):
    evidence_type: str = "pdf"
    page_number: int = Field(ge=1)
    bbox: PreviewBoundingBox
    label: str


class ExcelEvidenceHighlight(BaseModel):
    evidence_type: str = "excel"
    sheet_name: str
    cell_range: str
    label: str


EvidenceHighlight = PdfEvidenceHighlight | ExcelEvidenceHighlight


class Document(BaseModel):
    document_id: str
    client_id: str
    competence_id: str
    filename: str
    original_filename: str
    extension: str
    mime_type: str
    size_bytes: int = Field(ge=0)
    sha256_hash: str
    storage_bucket: str
    storage_key: str
    document_type: DocumentType
    status: DocumentStatus
    classification_confidence: float | None = Field(default=None, ge=0, le=1)
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

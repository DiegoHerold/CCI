from typing import Literal

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class PdfSelection(BaseModel):
    kind: Literal["pdf_text", "pdf_area"]
    page: int = Field(ge=1)
    selected_text: str | None = None
    bbox: BoundingBox


class ExcelSelection(BaseModel):
    kind: Literal["excel_cell", "excel_column", "excel_table"]
    sheet: str
    range: str
    header: str | None = None


class Annotation(BaseModel):
    annotation_id: str
    template_id: str
    template_version: int = Field(ge=1)
    document_id: str
    target_field: str
    selection: PdfSelection | ExcelSelection

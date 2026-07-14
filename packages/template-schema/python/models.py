from enum import Enum

from pydantic import BaseModel, Field


class TemplateFormat(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    IMAGE = "image"
    OTHER = "other"


class TemplateIdentificationSignal(BaseModel):
    kind: str
    value: str
    weight: float | None = Field(default=None, ge=0, le=1)


class TemplateVersion(BaseModel):
    template_id: str
    name: str
    category: str
    format: TemplateFormat
    structure_type: str
    version: int = Field(ge=1)
    status: str
    identification_signals: list[TemplateIdentificationSignal] = Field(default_factory=list)
    field_paths: list[str] = Field(default_factory=list)

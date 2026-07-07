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
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXTRACTED = "extracted"
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

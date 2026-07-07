from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VariableType(str, Enum):
    CURRENCY = "currency"
    NUMBER = "number"
    INTEGER = "integer"
    PERCENTAGE = "percentage"
    DATE = "date"
    COMPETENCE = "competence"
    TEXT = "text"
    BOOLEAN = "boolean"
    ACCOUNT_CODE = "account_code"
    CNPJ = "cnpj"
    CPF = "cpf"
    LIST = "list"
    OBJECT = "object"


class VariableStatus(str, Enum):
    EXTRACTED = "extracted"
    NORMALIZED = "normalized"
    CONFIRMED = "confirmed"
    CORRECTED = "corrected"
    IGNORED = "ignored"
    NEED_REVIEW = "need_review"
    USED_IN_RULE = "used_in_rule"


class Evidence(BaseModel):
    document_id: str
    page: int | None = Field(default=None, ge=1)
    row: int | None = Field(default=None, ge=1)
    column: str | None = None
    cell: str | None = None
    text: str | None = None
    bounding_box: dict[str, float] | None = None


class Variable(BaseModel):
    variable_id: str
    client_id: str
    competence_id: str
    document_id: str
    key: str
    label: str
    type: VariableType
    value: Any
    raw_value: Any
    status: VariableStatus
    confidence: float = Field(ge=0, le=1)
    evidence: Evidence
    created_at: datetime | None = None
    updated_at: datetime | None = None
    normalized_by: str | None = None
    confirmed_by: str | None = None

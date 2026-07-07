from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResultStatus(str, Enum):
    APPROVED = "approved"
    DIVERGENT = "divergent"
    ERROR = "error"
    PENDING = "pending"
    NOT_APPLICABLE = "not_applicable"
    NEEDS_REVIEW = "needs_review"


class RuleEvaluationResult(BaseModel):
    status: ResultStatus
    operator: str
    left_value: Any | None = None
    right_value: Any | None = None
    difference: float | None = None
    message: str
    details: list["RuleEvaluationResult"] = Field(default_factory=list)

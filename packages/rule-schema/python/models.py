from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class RuleOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"
    DIFFERENCE_LESS_THAN = "difference_less_than"
    SUM_EQUALS = "sum_equals"
    FORMULA = "formula"
    AND = "and"
    OR = "or"
    IF_THEN = "if_then"


class RuleLogic(BaseModel):
    operator: RuleOperator
    left: Any | None = None
    right: Any | None = None
    items: list[str] | None = None
    conditions: list["RuleLogic"] | None = None
    tolerance: float | None = Field(default=None, ge=0)


class Rule(BaseModel):
    rule_id: str
    client_id: str
    model_id: str
    name: str
    description: str
    version: int = Field(ge=1)
    status: RuleStatus
    logic: RuleLogic
    required_variables: list[str] = Field(default_factory=list)
    tolerance: float | None = Field(default=None, ge=0)
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    activated_at: datetime | None = None

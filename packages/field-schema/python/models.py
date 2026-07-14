from enum import Enum

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    MONEY = "money"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    OBJECT = "object"
    ARRAY = "array"
    TABLE = "table"
    CALCULATED = "calculated"


class FieldDefinition(BaseModel):
    field_id: str
    path: str
    label: str
    field_type: FieldType
    required: bool = False
    children: list["FieldDefinition"] = Field(default_factory=list)
    formula: str | None = None

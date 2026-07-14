from enum import Enum

from pydantic import BaseModel, Field


class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    MONEY = "money"
    DATE = "date"
    MONTH = "month"
    CNPJ = "cnpj"
    CPF = "cpf"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    TABLE = "table"
    CALCULATED = "calculated"
    UNKNOWN = "unknown"


class FieldPath(BaseModel):
    value: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_]*(\[\])?(\.[A-Za-z_][A-Za-z0-9_]*(\[\])?)*$")


class FieldDefinition(BaseModel):
    id: str
    template_id: str
    parent_field_id: str | None = None
    field_path: str
    label: str
    description: str | None = None
    field_type: FieldType
    is_required: bool = False
    is_repeated: bool = False
    is_object: bool = False
    is_array: bool = False
    order_index: int = Field(default=0, ge=0)


class ObjectField(FieldDefinition):
    field_type: FieldType = FieldType.OBJECT
    is_object: bool = True


class ArrayField(FieldDefinition):
    field_type: FieldType = FieldType.ARRAY
    is_repeated: bool = True
    is_array: bool = True


class TableField(FieldDefinition):
    field_type: FieldType = FieldType.TABLE
    is_repeated: bool = True


class CalculatedField(FieldDefinition):
    field_type: FieldType = FieldType.CALCULATED
    formula: str | None = None


class FieldCard(BaseModel):
    field_id: str
    field_path: str
    label: str
    field_type: FieldType
    template_id: str
    is_repeated: bool = False
    evidence_required: bool = True


class FieldTreeNode(BaseModel):
    key: str
    label: str
    path: str
    field: FieldDefinition | None = None
    children: list["FieldTreeNode"] = Field(default_factory=list)


class CreateFieldRequest(BaseModel):
    parent_field_id: str | None = None
    field_path: str
    label: str
    description: str | None = None
    field_type: FieldType
    is_required: bool = False
    is_repeated: bool = False
    is_object: bool = False
    is_array: bool = False
    order_index: int = Field(default=0, ge=0)


class UpdateFieldRequest(BaseModel):
    parent_field_id: str | None = None
    label: str | None = None
    description: str | None = None
    field_type: FieldType | None = None
    is_required: bool | None = None
    is_repeated: bool | None = None
    is_object: bool | None = None
    is_array: bool | None = None
    order_index: int | None = Field(default=None, ge=0)


class FieldMappingStatus(str, Enum):
    UNMAPPED = "unmapped"
    MAPPED = "mapped"
    PARTIAL = "partial"

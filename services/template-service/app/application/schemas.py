from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import (
    AnnotationType,
    ExtractionStrategy,
    FieldType,
    IdentificationSignalType,
    TemplateFileFormat,
    TemplateStatus,
    TemplateStructureType,
    TemplateVersionStatus,
)
from app.infrastructure.database.models import (
    ExtractionRule,
    IdentificationSignal,
    Template,
    TemplateAnnotation,
    TemplateCategory,
    TemplateField,
    TemplateVersion,
)


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class TemplateCategoryCreate(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9][a-z0-9-]*$")
    description: str | None = None


class TemplateCategoryResponse(ApiModel):
    category_id: str
    name: str
    slug: str
    description: str | None = None
    status: TemplateStatus
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateCategory) -> "TemplateCategoryResponse":
        return cls(
            category_id=entity.id,
            name=entity.name,
            slug=entity.slug,
            description=entity.description,
            status=TemplateStatus(entity.status),
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateCategoryListResponse(ApiModel):
    items: list[TemplateCategoryResponse]


class TemplateCreate(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: str = Field(min_length=1, max_length=36)
    file_format: TemplateFileFormat
    structure_type: TemplateStructureType = TemplateStructureType.UNKNOWN


class TemplateUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category_id: str | None = Field(default=None, min_length=1, max_length=36)
    file_format: TemplateFileFormat | None = None
    structure_type: TemplateStructureType | None = None


class TemplateStatusUpdate(ApiModel):
    status: TemplateStatus


class FieldCreate(ApiModel):
    parent_field_id: str | None = Field(default=None, max_length=36)
    field_path: str = Field(min_length=1, max_length=512)
    label: str = Field(min_length=1, max_length=255)
    description: str | None = None
    field_type: FieldType
    is_required: bool = False
    is_repeated: bool = False
    is_object: bool = False
    is_array: bool = False
    order_index: int = Field(default=0, ge=0)


class FieldUpdate(ApiModel):
    parent_field_id: str | None = Field(default=None, max_length=36)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    field_type: FieldType | None = None
    is_required: bool | None = None
    is_repeated: bool | None = None
    is_object: bool | None = None
    is_array: bool | None = None
    order_index: int | None = Field(default=None, ge=0)


class FieldResponse(ApiModel):
    field_id: str
    template_id: str
    parent_field_id: str | None = None
    field_path: str
    label: str
    description: str | None = None
    field_type: FieldType
    is_required: bool
    is_repeated: bool
    is_object: bool
    is_array: bool
    order_index: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateField) -> "FieldResponse":
        return cls(
            field_id=entity.id,
            template_id=entity.template_id,
            parent_field_id=entity.parent_field_id,
            field_path=entity.field_path,
            label=entity.label,
            description=entity.description,
            field_type=FieldType(entity.field_type),
            is_required=entity.is_required,
            is_repeated=entity.is_repeated,
            is_object=entity.is_object,
            is_array=entity.is_array,
            order_index=entity.order_index,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class IdentificationSignalCreate(ApiModel):
    signal_type: IdentificationSignalType
    value: str = Field(min_length=1)
    weight: float = Field(default=1.0, ge=0, le=100)
    required: bool = False
    negative: bool = False


class IdentificationSignalUpdate(ApiModel):
    signal_type: IdentificationSignalType | None = None
    value: str | None = Field(default=None, min_length=1)
    weight: float | None = Field(default=None, ge=0, le=100)
    required: bool | None = None
    negative: bool | None = None


class IdentificationSignalResponse(ApiModel):
    signal_id: str
    template_id: str
    signal_type: IdentificationSignalType
    value: str
    weight: float
    required: bool
    negative: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: IdentificationSignal) -> "IdentificationSignalResponse":
        return cls(
            signal_id=entity.id,
            template_id=entity.template_id,
            signal_type=IdentificationSignalType(entity.signal_type),
            value=entity.value,
            weight=entity.weight,
            required=entity.required,
            negative=entity.negative,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class AnnotationCreate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    field_id: str = Field(min_length=1, max_length=36)
    document_id: str = Field(min_length=1, max_length=36)
    annotation_type: AnnotationType
    source_preview_id: str | None = Field(default=None, max_length=36)
    selected_text: str | None = None
    selection_payload: dict[str, Any]


class AnnotationResponse(ApiModel):
    annotation_id: str
    template_id: str
    template_version_id: str | None = None
    field_id: str
    document_id: str
    annotation_type: AnnotationType
    source_preview_id: str | None = None
    selected_text: str | None = None
    selection_payload: dict[str, Any]
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateAnnotation) -> "AnnotationResponse":
        return cls(
            annotation_id=entity.id,
            template_id=entity.template_id,
            template_version_id=entity.template_version_id,
            field_id=entity.field_id,
            document_id=entity.document_id,
            annotation_type=AnnotationType(entity.annotation_type),
            source_preview_id=entity.source_preview_id,
            selected_text=entity.selected_text,
            selection_payload=entity.selection_payload,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class ExtractionRuleCreate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    field_id: str = Field(min_length=1, max_length=36)
    rule_type: str | None = Field(default=None, max_length=64)
    strategy: ExtractionStrategy
    config: dict[str, Any] = Field(default_factory=dict)
    confidence_hint: float | None = Field(default=None, ge=0, le=1)
    created_from_annotation_id: str | None = Field(default=None, max_length=36)


class ExtractionRuleUpdate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    rule_type: str | None = Field(default=None, max_length=64)
    strategy: ExtractionStrategy | None = None
    config: dict[str, Any] | None = None
    confidence_hint: float | None = Field(default=None, ge=0, le=1)
    created_from_annotation_id: str | None = Field(default=None, max_length=36)


class ExtractionRuleResponse(ApiModel):
    rule_id: str
    template_id: str
    template_version_id: str | None = None
    field_id: str
    rule_type: str | None = None
    strategy: ExtractionStrategy
    config: dict[str, Any]
    confidence_hint: float | None = None
    created_from_annotation_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: ExtractionRule) -> "ExtractionRuleResponse":
        return cls(
            rule_id=entity.id,
            template_id=entity.template_id,
            template_version_id=entity.template_version_id,
            field_id=entity.field_id,
            rule_type=entity.rule_type,
            strategy=ExtractionStrategy(entity.strategy),
            config=entity.config,
            confidence_hint=entity.confidence_hint,
            created_from_annotation_id=entity.created_from_annotation_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateVersionCreate(ApiModel):
    base_version_id: str | None = Field(default=None, max_length=36)


class TemplateVersionResponse(ApiModel):
    version_id: str
    template_id: str
    version_number: int
    status: TemplateVersionStatus
    snapshot: dict[str, Any]
    created_by: str
    published_by: str | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateVersion) -> "TemplateVersionResponse":
        return cls(
            version_id=entity.id,
            template_id=entity.template_id,
            version_number=entity.version_number,
            status=TemplateVersionStatus(entity.status),
            snapshot=entity.snapshot,
            created_by=entity.created_by,
            published_by=entity.published_by,
            published_at=entity.published_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class PublishVersionResponse(ApiModel):
    template_id: str
    version_id: str
    version_number: int
    status: TemplateVersionStatus
    active: bool


class TemplateSummary(ApiModel):
    template_id: str
    name: str
    description: str | None = None
    category_id: str
    file_format: TemplateFileFormat
    structure_type: TemplateStructureType
    status: TemplateStatus
    active_version_id: str | None = None
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: Template) -> "TemplateSummary":
        return cls(
            template_id=entity.id,
            name=entity.name,
            description=entity.description,
            category_id=entity.category_id,
            file_format=TemplateFileFormat(entity.file_format),
            structure_type=TemplateStructureType(entity.structure_type),
            status=TemplateStatus(entity.status),
            active_version_id=entity.active_version_id,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateDetail(TemplateSummary):
    category: TemplateCategoryResponse | None = None
    fields: list[FieldResponse] = Field(default_factory=list)
    identification_signals: list[IdentificationSignalResponse] = Field(default_factory=list)
    annotations: list[AnnotationResponse] = Field(default_factory=list)
    extraction_rules: list[ExtractionRuleResponse] = Field(default_factory=list)
    versions: list[TemplateVersionResponse] = Field(default_factory=list)

    @classmethod
    def from_entity(cls, entity: Template) -> "TemplateDetail":
        summary = TemplateSummary.from_entity(entity).model_dump()
        return cls(
            **summary,
            category=TemplateCategoryResponse.from_entity(entity.category) if entity.category else None,
            fields=[FieldResponse.from_entity(item) for item in entity.fields],
            identification_signals=[
                IdentificationSignalResponse.from_entity(item)
                for item in entity.identification_signals
            ],
            annotations=[AnnotationResponse.from_entity(item) for item in entity.annotations],
            extraction_rules=[
                ExtractionRuleResponse.from_entity(item) for item in entity.extraction_rules
            ],
            versions=[TemplateVersionResponse.from_entity(item) for item in entity.versions],
        )


class TemplateListResponse(ApiModel):
    items: list[TemplateSummary]
    total: int


class FieldListResponse(ApiModel):
    items: list[FieldResponse]


class IdentificationSignalListResponse(ApiModel):
    items: list[IdentificationSignalResponse]


class AnnotationListResponse(ApiModel):
    items: list[AnnotationResponse]


class ExtractionRuleListResponse(ApiModel):
    items: list[ExtractionRuleResponse]


class TemplateVersionListResponse(ApiModel):
    items: list[TemplateVersionResponse]
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import (
    AnnotationType,
    ExtractionStrategy,
    FieldType,
    IdentificationSignalType,
    TemplateFileFormat,
    TemplateStatus,
    TemplateStructureType,
    TemplateVersionStatus,
)
from app.infrastructure.database.models import (
    ExtractionRule,
    IdentificationSignal,
    Template,
    TemplateAnnotation,
    TemplateCategory,
    TemplateField,
    TemplateVersion,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class TemplateCategoryCreate(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    description: str | None = Field(default=None, max_length=4096)


class TemplateCategoryResponse(ApiModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateCategory) -> "TemplateCategoryResponse":
        return cls.model_validate(entity)


class TemplateCategoryListResponse(ApiModel):
    items: list[TemplateCategoryResponse]


class TemplateCreate(ApiModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    category_id: str = Field(min_length=1, max_length=36)
    file_format: TemplateFileFormat
    structure_type: TemplateStructureType


class TemplateUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    category_id: str | None = Field(default=None, min_length=1, max_length=36)
    file_format: TemplateFileFormat | None = None
    structure_type: TemplateStructureType | None = None


class TemplateStatusUpdate(ApiModel):
    status: TemplateStatus


class TemplateSummary(ApiModel):
    template_id: str
    name: str
    description: str | None = None
    category_id: str
    file_format: TemplateFileFormat
    structure_type: TemplateStructureType
    status: TemplateStatus
    active_version_id: str | None = None
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: Template) -> "TemplateSummary":
        return cls(
            template_id=entity.id,
            name=entity.name,
            description=entity.description,
            category_id=entity.category_id,
            file_format=TemplateFileFormat(entity.file_format),
            structure_type=TemplateStructureType(entity.structure_type),
            status=TemplateStatus(entity.status),
            active_version_id=entity.active_version_id,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateListResponse(ApiModel):
    items: list[TemplateSummary]
    total: int


class FieldCreate(ApiModel):
    parent_field_id: str | None = Field(default=None, max_length=36)
    field_path: str = Field(min_length=1, max_length=512)
    label: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    field_type: FieldType
    is_required: bool = False
    is_repeated: bool = False
    is_object: bool = False
    is_array: bool = False
    order_index: int = Field(default=0, ge=0)

    @field_validator("field_path")
    @classmethod
    def validate_field_path(cls, value: str) -> str:
        parts = value.split(".")
        if any(not part for part in parts):
            raise ValueError("field_path must not contain empty path parts")
        return value


class FieldUpdate(ApiModel):
    parent_field_id: str | None = Field(default=None, max_length=36)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    field_type: FieldType | None = None
    is_required: bool | None = None
    is_repeated: bool | None = None
    is_object: bool | None = None
    is_array: bool | None = None
    order_index: int | None = Field(default=None, ge=0)


class FieldResponse(ApiModel):
    id: str
    template_id: str
    parent_field_id: str | None = None
    field_path: str
    label: str
    description: str | None = None
    field_type: FieldType
    is_required: bool
    is_repeated: bool
    is_object: bool
    is_array: bool
    order_index: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateField) -> "FieldResponse":
        return cls(
            id=entity.id,
            template_id=entity.template_id,
            parent_field_id=entity.parent_field_id,
            field_path=entity.field_path,
            label=entity.label,
            description=entity.description,
            field_type=FieldType(entity.field_type),
            is_required=entity.is_required,
            is_repeated=entity.is_repeated,
            is_object=entity.is_object,
            is_array=entity.is_array,
            order_index=entity.order_index,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class FieldListResponse(ApiModel):
    items: list[FieldResponse]


class IdentificationSignalCreate(ApiModel):
    signal_type: IdentificationSignalType
    weight: float = Field(default=1.0, ge=0, le=100)
    value: str = Field(min_length=1, max_length=4096)
    required: bool = False
    negative: bool = False


class IdentificationSignalUpdate(ApiModel):
    signal_type: IdentificationSignalType | None = None
    weight: float | None = Field(default=None, ge=0, le=100)
    value: str | None = Field(default=None, min_length=1, max_length=4096)
    required: bool | None = None
    negative: bool | None = None


class IdentificationSignalResponse(ApiModel):
    id: str
    template_id: str
    signal_type: IdentificationSignalType
    weight: float
    value: str
    required: bool
    negative: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: IdentificationSignal) -> "IdentificationSignalResponse":
        return cls(
            id=entity.id,
            template_id=entity.template_id,
            signal_type=IdentificationSignalType(entity.signal_type),
            weight=entity.weight,
            value=entity.value,
            required=entity.required,
            negative=entity.negative,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class IdentificationSignalListResponse(ApiModel):
    items: list[IdentificationSignalResponse]


class AnnotationCreate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    field_id: str = Field(min_length=1, max_length=36)
    document_id: str = Field(min_length=1, max_length=36)
    source_preview_id: str | None = Field(default=None, max_length=36)
    annotation_type: AnnotationType
    selected_text: str | None = Field(default=None, max_length=16384)
    selection_payload: dict[str, Any]


class AnnotationResponse(ApiModel):
    id: str
    template_id: str
    template_version_id: str | None = None
    field_id: str
    document_id: str
    annotation_type: AnnotationType
    source_preview_id: str | None = None
    selected_text: str | None = None
    selection_payload: dict[str, Any]
    created_by: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateAnnotation) -> "AnnotationResponse":
        return cls(
            id=entity.id,
            template_id=entity.template_id,
            template_version_id=entity.template_version_id,
            field_id=entity.field_id,
            document_id=entity.document_id,
            annotation_type=AnnotationType(entity.annotation_type),
            source_preview_id=entity.source_preview_id,
            selected_text=entity.selected_text,
            selection_payload=entity.selection_payload,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class AnnotationListResponse(ApiModel):
    items: list[AnnotationResponse]


class ExtractionRuleCreate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    field_id: str = Field(min_length=1, max_length=36)
    rule_type: str | None = Field(default=None, max_length=64)
    strategy: ExtractionStrategy
    config: dict[str, Any] = Field(default_factory=dict)
    confidence_hint: float | None = Field(default=None, ge=0, le=1)
    created_from_annotation_id: str | None = Field(default=None, max_length=36)


class ExtractionRuleUpdate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    rule_type: str | None = Field(default=None, max_length=64)
    strategy: ExtractionStrategy | None = None
    config: dict[str, Any] | None = None
    confidence_hint: float | None = Field(default=None, ge=0, le=1)
    created_from_annotation_id: str | None = Field(default=None, max_length=36)


class ExtractionRuleResponse(ApiModel):
    id: str
    template_id: str
    template_version_id: str | None = None
    field_id: str
    rule_type: str | None = None
    strategy: ExtractionStrategy
    config: dict[str, Any]
    confidence_hint: float | None = None
    created_from_annotation_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: ExtractionRule) -> "ExtractionRuleResponse":
        return cls(
            id=entity.id,
            template_id=entity.template_id,
            template_version_id=entity.template_version_id,
            field_id=entity.field_id,
            rule_type=entity.rule_type,
            strategy=ExtractionStrategy(entity.strategy),
            config=entity.config,
            confidence_hint=entity.confidence_hint,
            created_from_annotation_id=entity.created_from_annotation_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class ExtractionRuleListResponse(ApiModel):
    items: list[ExtractionRuleResponse]


class TemplateVersionCreate(ApiModel):
    base_version_id: str | None = Field(default=None, max_length=36)


class TemplateVersionResponse(ApiModel):
    id: str
    template_id: str
    version_number: int
    status: TemplateVersionStatus
    snapshot: dict[str, Any]
    created_by: str
    published_by: str | None = None
    published_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: TemplateVersion) -> "TemplateVersionResponse":
        return cls(
            id=entity.id,
            template_id=entity.template_id,
            version_number=entity.version_number,
            status=TemplateVersionStatus(entity.status),
            snapshot=entity.snapshot,
            created_by=entity.created_by,
            published_by=entity.published_by,
            published_at=entity.published_at,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateVersionListResponse(ApiModel):
    items: list[TemplateVersionResponse]


class PublishVersionResponse(ApiModel):
    template_id: str
    version_id: str
    version_number: int
    status: TemplateVersionStatus
    active: bool


class TemplateDetail(TemplateSummary):
    category: TemplateCategoryResponse | None = None
    fields: list[FieldResponse] = Field(default_factory=list)
    identification_signals: list[IdentificationSignalResponse] = Field(default_factory=list)
    annotations: list[AnnotationResponse] = Field(default_factory=list)
    extraction_rules: list[ExtractionRuleResponse] = Field(default_factory=list)
    versions: list[TemplateVersionResponse] = Field(default_factory=list)

    @classmethod
    def from_entity(cls, entity: Template) -> "TemplateDetail":
        summary = TemplateSummary.from_entity(entity)
        return cls(
            **summary.model_dump(),
            category=TemplateCategoryResponse.from_entity(entity.category) if entity.category else None,
            fields=[FieldResponse.from_entity(item) for item in entity.fields if item.status == "active"],
            identification_signals=[
                IdentificationSignalResponse.from_entity(item)
                for item in entity.identification_signals
            ],
            annotations=[AnnotationResponse.from_entity(item) for item in entity.annotations],
            extraction_rules=[ExtractionRuleResponse.from_entity(item) for item in entity.extraction_rules],
            versions=[TemplateVersionResponse.from_entity(item) for item in entity.versions],
        )


class TemplateMatchingRequest(ApiModel):
    force_reprocess: bool = False
    category_hint: str | None = Field(default=None, max_length=36)
    max_candidates: int | None = Field(default=None, ge=1, le=100)


class TemplateMatchConfirmRequest(ApiModel):
    template_id: str = Field(min_length=1, max_length=36)
    template_version_id: str = Field(min_length=1, max_length=36)
    reason: str = Field(min_length=1, max_length=4096)


class DocumentProfileResponse(ApiModel):
    id: str
    document_id: str
    file_format: str
    profile_version: str
    profile_json: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TemplateMatchingCandidateResponse(ApiModel):
    id: str
    matching_run_id: str
    template_id: str
    template_version_id: str | None = None
    category_id: str | None = None
    template_name: str | None = None
    category_name: str | None = None
    score: float
    rank_position: int
    matched_signals: list[str] = Field(default_factory=list)
    missing_required_signals: list[str] = Field(default_factory=list)
    negative_matches: list[str] = Field(default_factory=list)
    score_details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: Any) -> "TemplateMatchingCandidateResponse":
        return cls(
            id=entity.id,
            matching_run_id=entity.matching_run_id,
            template_id=entity.template_id,
            template_version_id=entity.template_version_id,
            category_id=entity.category_id,
            template_name=entity.template.name if getattr(entity, "template", None) else None,
            category_name=entity.category.name if getattr(entity, "category", None) else None,
            score=entity.score,
            rank_position=entity.rank_position,
            matched_signals=entity.matched_signals or [],
            missing_required_signals=entity.missing_required_signals or [],
            negative_matches=entity.negative_matches or [],
            score_details=entity.score_details or {},
            created_at=entity.created_at,
        )


class TemplateMatchingRunResponse(ApiModel):
    matching_run_id: str
    document_id: str
    status: str
    matched_template_id: str | None = None
    matched_template_version_id: str | None = None
    matched_category_id: str | None = None
    confidence: float
    decision_reason: str
    manual_override: bool = False
    candidates: list[TemplateMatchingCandidateResponse] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: Any) -> "TemplateMatchingRunResponse":
        return cls(
            matching_run_id=entity.id,
            document_id=entity.document_id,
            status=entity.status,
            matched_template_id=entity.matched_template_id,
            matched_template_version_id=entity.matched_template_version_id,
            matched_category_id=entity.matched_category_id,
            confidence=entity.confidence,
            decision_reason=entity.decision_reason,
            manual_override=entity.manual_override,
            candidates=[
                TemplateMatchingCandidateResponse.from_entity(candidate)
                for candidate in sorted(entity.candidates, key=lambda item: item.rank_position)
            ],
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class TemplateMatchingRunListResponse(ApiModel):
    items: list[TemplateMatchingRunResponse]


class AnnotationUpdate(ApiModel):
    template_version_id: str | None = Field(default=None, max_length=36)
    field_id: str | None = Field(default=None, min_length=1, max_length=36)
    source_preview_id: str | None = Field(default=None, max_length=36)
    selected_text: str | None = Field(default=None, max_length=16384)
    selection_payload: dict[str, Any] | None = None


class AnnotationWithRuleCreate(AnnotationCreate):
    generate_rule: bool = True
    rule_strategy: ExtractionStrategy | None = None
    rule_config: dict[str, Any] | None = None
    confidence_hint: float | None = Field(default=None, ge=0, le=1)


class AnnotationWithRuleResponse(ApiModel):
    annotation: AnnotationResponse
    extraction_rule: ExtractionRuleResponse | None = None
    suggested_strategy: ExtractionStrategy | None = None
    suggested_config: dict[str, Any] = Field(default_factory=dict)


class TemplateBuilderStateResponse(ApiModel):
    template: TemplateDetail
    active_version: TemplateVersionResponse | None = None
    draft_version: TemplateVersionResponse | None = None
    fields: list[FieldResponse] = Field(default_factory=list)
    annotations: list[AnnotationResponse] = Field(default_factory=list)
    extraction_rules: list[ExtractionRuleResponse] = Field(default_factory=list)
    identification_signals: list[IdentificationSignalResponse] = Field(default_factory=list)

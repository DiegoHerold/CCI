from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


def new_id() -> str:
    return str(uuid4())


class TemplateCategory(Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_template_categories_slug"),
        Index("ix_template_categories_status", "status"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    templates: Mapped[list["Template"]] = relationship(back_populates="category")


class Template(Base):
    __tablename__ = "templates"
    __table_args__ = (
        Index("ix_template_templates_category", "category_id"),
        Index("ix_template_templates_file_format", "file_format"),
        Index("ix_template_templates_status", "status"),
        Index("ix_template_templates_structure_type", "structure_type"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.categories.id", ondelete="RESTRICT"), nullable=False
    )
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)
    structure_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    active_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    category: Mapped[TemplateCategory] = relationship(back_populates="templates")
    fields: Mapped[list["TemplateField"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    identification_signals: Mapped[list["IdentificationSignal"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    annotations: Mapped[list["TemplateAnnotation"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    extraction_rules: Mapped[list["ExtractionRule"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )
    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class TemplateField(Base):
    __tablename__ = "template_fields"
    __table_args__ = (
        UniqueConstraint("template_id", "field_path", name="uq_template_fields_template_path"),
        Index("ix_template_fields_template", "template_id"),
        Index("ix_template_fields_parent", "parent_field_id"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.templates.id", ondelete="CASCADE"), nullable=False
    )
    parent_field_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("template.template_fields.id", ondelete="RESTRICT"), nullable=True
    )
    field_path: Mapped[str] = mapped_column(String(512), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    field_type: Mapped[str] = mapped_column(String(32), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_repeated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_object: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_array: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Template] = relationship(back_populates="fields")
    parent: Mapped["TemplateField | None"] = relationship(remote_side=[id])


class IdentificationSignal(Base):
    __tablename__ = "identification_signals"
    __table_args__ = (
        Index("ix_template_identification_signals_template", "template_id"),
        Index("ix_template_identification_signals_type", "signal_type"),
        Index("ix_template_identification_signals_required", "required"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.templates.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    negative: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Template] = relationship(back_populates="identification_signals")


class TemplateVersion(Base):
    __tablename__ = "template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version_number", name="uq_template_versions_number"),
        Index("ix_template_versions_template", "template_id"),
        Index("ix_template_versions_status", "status"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.templates.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    published_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Template] = relationship(back_populates="versions")


class TemplateAnnotation(Base):
    __tablename__ = "template_annotations"
    __table_args__ = (
        Index("ix_template_annotations_template", "template_id"),
        Index("ix_template_annotations_field", "field_id"),
        Index("ix_template_annotations_document", "document_id"),
        Index("ix_template_annotations_type", "annotation_type"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.templates.id", ondelete="CASCADE"), nullable=False
    )
    template_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("template.template_versions.id", ondelete="SET NULL"), nullable=True
    )
    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.template_fields.id", ondelete="RESTRICT"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_preview_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    selected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    selection_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Template] = relationship(back_populates="annotations")
    field: Mapped[TemplateField] = relationship()
    template_version: Mapped[TemplateVersion | None] = relationship()


class ExtractionRule(Base):
    __tablename__ = "extraction_rules"
    __table_args__ = (
        Index("ix_template_extraction_rules_template", "template_id"),
        Index("ix_template_extraction_rules_field", "field_id"),
        Index("ix_template_extraction_rules_strategy", "strategy"),
        Index("ix_template_extraction_rules_annotation", "created_from_annotation_id"),
        {"schema": "template"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.templates.id", ondelete="CASCADE"), nullable=False
    )
    template_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("template.template_versions.id", ondelete="SET NULL"), nullable=True
    )
    field_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("template.template_fields.id", ondelete="RESTRICT"), nullable=False
    )
    rule_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_hint: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_from_annotation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("template.template_annotations.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Template] = relationship(back_populates="extraction_rules")
    field: Mapped[TemplateField] = relationship()
    template_version: Mapped[TemplateVersion | None] = relationship()
    created_from_annotation: Mapped[TemplateAnnotation | None] = relationship()

"""template domain

Revision ID: 0001_template_domain
Revises:
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001_template_domain"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS template")
    op.create_table(
        "categories",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_template_categories_slug"),
        schema="template",
    )
    op.create_index("ix_template_categories_status", "categories", ["status"], schema="template")

    op.create_table(
        "templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.String(length=36), nullable=False),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("structure_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("active_version_id", sa.String(length=36), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["template.categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_templates_category", "templates", ["category_id"], schema="template")
    op.create_index("ix_template_templates_file_format", "templates", ["file_format"], schema="template")
    op.create_index("ix_template_templates_status", "templates", ["status"], schema="template")
    op.create_index("ix_template_templates_structure_type", "templates", ["structure_type"], schema="template")

    op.create_table(
        "template_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("published_by", sa.String(length=36), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "version_number", name="uq_template_versions_number"),
        schema="template",
    )
    op.create_index("ix_template_versions_template", "template_versions", ["template_id"], schema="template")
    op.create_index("ix_template_versions_status", "template_versions", ["status"], schema="template")

    op.create_table(
        "template_fields",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("parent_field_id", sa.String(length=36), nullable=True),
        sa.Column("field_path", sa.String(length=512), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("field_type", sa.String(length=32), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_repeated", sa.Boolean(), nullable=False),
        sa.Column("is_object", sa.Boolean(), nullable=False),
        sa.Column("is_array", sa.Boolean(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_field_id"], ["template.template_fields.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "field_path", name="uq_template_fields_template_path"),
        schema="template",
    )
    op.create_index("ix_template_fields_template", "template_fields", ["template_id"], schema="template")
    op.create_index("ix_template_fields_parent", "template_fields", ["parent_field_id"], schema="template")

    op.create_table(
        "identification_signals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("negative", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_identification_signals_template", "identification_signals", ["template_id"], schema="template")
    op.create_index("ix_template_identification_signals_type", "identification_signals", ["signal_type"], schema="template")
    op.create_index("ix_template_identification_signals_required", "identification_signals", ["required"], schema="template")

    op.create_table(
        "template_annotations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=True),
        sa.Column("field_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("annotation_type", sa.String(length=64), nullable=False),
        sa.Column("source_preview_id", sa.String(length=36), nullable=True),
        sa.Column("selected_text", sa.Text(), nullable=True),
        sa.Column("selection_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["field_id"], ["template.template_fields.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_version_id"], ["template.template_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_annotations_template", "template_annotations", ["template_id"], schema="template")
    op.create_index("ix_template_annotations_field", "template_annotations", ["field_id"], schema="template")
    op.create_index("ix_template_annotations_document", "template_annotations", ["document_id"], schema="template")
    op.create_index("ix_template_annotations_type", "template_annotations", ["annotation_type"], schema="template")

    op.create_table(
        "extraction_rules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=True),
        sa.Column("field_id", sa.String(length=36), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=True),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence_hint", sa.Float(), nullable=True),
        sa.Column("created_from_annotation_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_from_annotation_id"], ["template.template_annotations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["field_id"], ["template.template_fields.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_version_id"], ["template.template_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_extraction_rules_template", "extraction_rules", ["template_id"], schema="template")
    op.create_index("ix_template_extraction_rules_field", "extraction_rules", ["field_id"], schema="template")
    op.create_index("ix_template_extraction_rules_strategy", "extraction_rules", ["strategy"], schema="template")
    op.create_index("ix_template_extraction_rules_annotation", "extraction_rules", ["created_from_annotation_id"], schema="template")


def downgrade() -> None:
    op.drop_index("ix_template_extraction_rules_annotation", table_name="extraction_rules", schema="template")
    op.drop_index("ix_template_extraction_rules_strategy", table_name="extraction_rules", schema="template")
    op.drop_index("ix_template_extraction_rules_field", table_name="extraction_rules", schema="template")
    op.drop_index("ix_template_extraction_rules_template", table_name="extraction_rules", schema="template")
    op.drop_table("extraction_rules", schema="template")
    op.drop_index("ix_template_annotations_type", table_name="template_annotations", schema="template")
    op.drop_index("ix_template_annotations_document", table_name="template_annotations", schema="template")
    op.drop_index("ix_template_annotations_field", table_name="template_annotations", schema="template")
    op.drop_index("ix_template_annotations_template", table_name="template_annotations", schema="template")
    op.drop_table("template_annotations", schema="template")
    op.drop_index("ix_template_identification_signals_required", table_name="identification_signals", schema="template")
    op.drop_index("ix_template_identification_signals_type", table_name="identification_signals", schema="template")
    op.drop_index("ix_template_identification_signals_template", table_name="identification_signals", schema="template")
    op.drop_table("identification_signals", schema="template")
    op.drop_index("ix_template_fields_parent", table_name="template_fields", schema="template")
    op.drop_index("ix_template_fields_template", table_name="template_fields", schema="template")
    op.drop_table("template_fields", schema="template")
    op.drop_index("ix_template_versions_status", table_name="template_versions", schema="template")
    op.drop_index("ix_template_versions_template", table_name="template_versions", schema="template")
    op.drop_table("template_versions", schema="template")
    op.drop_index("ix_template_templates_structure_type", table_name="templates", schema="template")
    op.drop_index("ix_template_templates_status", table_name="templates", schema="template")
    op.drop_index("ix_template_templates_file_format", table_name="templates", schema="template")
    op.drop_index("ix_template_templates_category", table_name="templates", schema="template")
    op.drop_table("templates", schema="template")
    op.drop_index("ix_template_categories_status", table_name="categories", schema="template")
    op.drop_table("categories", schema="template")

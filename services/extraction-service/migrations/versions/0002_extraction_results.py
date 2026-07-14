"""extraction results

Revision ID: 0002_extraction_results
Revises: 0001_extraction_jobs
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_extraction_results"
down_revision: Union[str, None] = "0001_extraction_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extraction_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_job_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("competence_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("field_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("normalized_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requires_review_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("warning_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["extraction.extraction_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_results_job", "extraction_results", ["extraction_job_id"], schema="extraction")
    op.create_index("ix_extraction_results_document", "extraction_results", ["document_id"], schema="extraction")
    op.create_index("ix_extraction_results_client_competence", "extraction_results", ["client_id", "competence_id"], schema="extraction")
    op.create_index("ix_extraction_results_template", "extraction_results", ["template_id"], schema="extraction")
    op.create_index("ix_extraction_results_template_version", "extraction_results", ["template_version_id"], schema="extraction")
    op.create_index("ix_extraction_results_status", "extraction_results", ["status"], schema="extraction")
    op.create_index("ix_extraction_results_created", "extraction_results", ["created_at"], schema="extraction")

    op.create_table(
        "extracted_objects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=False),
        sa.Column("parent_object_id", sa.String(length=36), nullable=True),
        sa.Column("field_path", sa.String(length=512), nullable=False),
        sa.Column("field_type", sa.String(length=64), nullable=False),
        sa.Column("object_type", sa.String(length=64), nullable=True),
        sa.Column("item_index", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_object_id"], ["extraction.extracted_objects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extracted_objects_result", "extracted_objects", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_extracted_objects_parent", "extracted_objects", ["parent_object_id"], schema="extraction")
    op.create_index("ix_extracted_objects_path", "extracted_objects", ["field_path"], schema="extraction")

    op.create_table(
        "extracted_array_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=False),
        sa.Column("array_field_path", sa.String(length=512), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extracted_array_items_result", "extracted_array_items", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_extracted_array_items_path", "extracted_array_items", ["array_field_path"], schema="extraction")
    op.create_index("ix_extracted_array_items_result_path_index", "extracted_array_items", ["extraction_result_id", "array_field_path", "item_index"], schema="extraction")

    op.create_table(
        "extracted_field_values",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=False),
        sa.Column("extracted_object_id", sa.String(length=36), nullable=True),
        sa.Column("field_id", sa.String(length=36), nullable=True),
        sa.Column("field_path", sa.String(length=512), nullable=False),
        sa.Column("field_type", sa.String(length=64), nullable=False),
        sa.Column("raw_value", sa.JSON(), nullable=True),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("display_value", sa.Text(), nullable=True),
        sa.Column("normalized_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("evidence_id", sa.String(length=36), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("item_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["extracted_object_id"], ["extraction.extracted_objects.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extracted_field_values_result", "extracted_field_values", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_extracted_field_values_path", "extracted_field_values", ["field_path"], schema="extraction")
    op.create_index("ix_extracted_field_values_field", "extracted_field_values", ["field_id"], schema="extraction")
    op.create_index("ix_extracted_field_values_status", "extracted_field_values", ["status"], schema="extraction")
    op.create_index("ix_extracted_field_values_confidence", "extracted_field_values", ["confidence"], schema="extraction")
    op.create_index("ix_extracted_field_values_item", "extracted_field_values", ["item_index"], schema="extraction")

    op.create_table(
        "extraction_evidences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("field_value_id", sa.String(length=36), nullable=True),
        sa.Column("evidence_type", sa.String(length=32), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("bbox_json", sa.JSON(), nullable=True),
        sa.Column("sheet_name", sa.String(length=255), nullable=True),
        sa.Column("cell_range", sa.String(length=255), nullable=True),
        sa.Column("source_text", sa.Text(), nullable=True),
        sa.Column("source_value", sa.JSON(), nullable=True),
        sa.Column("rule_id", sa.String(length=36), nullable=True),
        sa.Column("rule_strategy", sa.String(length=128), nullable=True),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_value_id"], ["extraction.extracted_field_values.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_evidences_result", "extraction_evidences", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_extraction_evidences_document", "extraction_evidences", ["document_id"], schema="extraction")
    op.create_index("ix_extraction_evidences_field", "extraction_evidences", ["field_value_id"], schema="extraction")
    op.create_index("ix_extraction_evidences_type", "extraction_evidences", ["evidence_type"], schema="extraction")
    op.create_index("ix_extraction_evidences_rule", "extraction_evidences", ["rule_id"], schema="extraction")

    op.create_table(
        "normalization_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_job_id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["extraction.extraction_jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_normalization_runs_job", "normalization_runs", ["extraction_job_id"], schema="extraction")
    op.create_index("ix_normalization_runs_result", "normalization_runs", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_normalization_runs_status", "normalization_runs", ["status"], schema="extraction")


def downgrade() -> None:
    op.drop_index("ix_normalization_runs_status", table_name="normalization_runs", schema="extraction")
    op.drop_index("ix_normalization_runs_result", table_name="normalization_runs", schema="extraction")
    op.drop_index("ix_normalization_runs_job", table_name="normalization_runs", schema="extraction")
    op.drop_table("normalization_runs", schema="extraction")
    op.drop_index("ix_extraction_evidences_rule", table_name="extraction_evidences", schema="extraction")
    op.drop_index("ix_extraction_evidences_type", table_name="extraction_evidences", schema="extraction")
    op.drop_index("ix_extraction_evidences_field", table_name="extraction_evidences", schema="extraction")
    op.drop_index("ix_extraction_evidences_document", table_name="extraction_evidences", schema="extraction")
    op.drop_index("ix_extraction_evidences_result", table_name="extraction_evidences", schema="extraction")
    op.drop_table("extraction_evidences", schema="extraction")
    op.drop_index("ix_extracted_field_values_item", table_name="extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_field_values_confidence", table_name="extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_field_values_status", table_name="extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_field_values_field", table_name="extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_field_values_path", table_name="extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_field_values_result", table_name="extracted_field_values", schema="extraction")
    op.drop_table("extracted_field_values", schema="extraction")
    op.drop_index("ix_extracted_array_items_result_path_index", table_name="extracted_array_items", schema="extraction")
    op.drop_index("ix_extracted_array_items_path", table_name="extracted_array_items", schema="extraction")
    op.drop_index("ix_extracted_array_items_result", table_name="extracted_array_items", schema="extraction")
    op.drop_table("extracted_array_items", schema="extraction")
    op.drop_index("ix_extracted_objects_path", table_name="extracted_objects", schema="extraction")
    op.drop_index("ix_extracted_objects_parent", table_name="extracted_objects", schema="extraction")
    op.drop_index("ix_extracted_objects_result", table_name="extracted_objects", schema="extraction")
    op.drop_table("extracted_objects", schema="extraction")
    op.drop_index("ix_extraction_results_created", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_status", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_template_version", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_template", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_client_competence", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_document", table_name="extraction_results", schema="extraction")
    op.drop_index("ix_extraction_results_job", table_name="extraction_results", schema="extraction")
    op.drop_table("extraction_results", schema="extraction")

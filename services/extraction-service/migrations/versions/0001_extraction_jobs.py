"""extraction jobs

Revision ID: 0001_extraction_jobs
Revises: None
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_extraction_jobs"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS extraction")
    op.create_table(
        "extraction_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("competence_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=True),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("workflow_run_id", sa.String(length=255), nullable=True),
        sa.Column("requested_by", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_jobs_document", "extraction_jobs", ["document_id"], schema="extraction")
    op.create_index("ix_extraction_jobs_client_competence", "extraction_jobs", ["client_id", "competence_id"], schema="extraction")
    op.create_index("ix_extraction_jobs_template", "extraction_jobs", ["template_id"], schema="extraction")
    op.create_index("ix_extraction_jobs_template_version", "extraction_jobs", ["template_version_id"], schema="extraction")
    op.create_index("ix_extraction_jobs_status", "extraction_jobs", ["status"], schema="extraction")
    op.create_index("ix_extraction_jobs_created", "extraction_jobs", ["created_at"], schema="extraction")
    op.create_index("ix_extraction_jobs_workflow", "extraction_jobs", ["workflow_id"], schema="extraction")

    op.create_table(
        "extraction_job_status_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_job_id", sa.String(length=36), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", sa.String(length=128), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["extraction.extraction_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_status_history_job", "extraction_job_status_history", ["extraction_job_id"], schema="extraction")
    op.create_index("ix_extraction_status_history_changed", "extraction_job_status_history", ["changed_at"], schema="extraction")

    op.create_table(
        "extraction_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_job_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("worker_type", sa.String(length=64), nullable=True),
        sa.Column("worker_name", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["extraction.extraction_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_attempts_job", "extraction_attempts", ["extraction_job_id"], schema="extraction")
    op.create_index("ix_extraction_attempts_status", "extraction_attempts", ["status"], schema="extraction")

    op.create_table(
        "extraction_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_job_id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("storage_bucket", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_job_id"], ["extraction.extraction_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extraction_artifacts_job", "extraction_artifacts", ["extraction_job_id"], schema="extraction")
    op.create_index("ix_extraction_artifacts_document", "extraction_artifacts", ["document_id"], schema="extraction")


def downgrade() -> None:
    op.drop_index("ix_extraction_artifacts_document", table_name="extraction_artifacts", schema="extraction")
    op.drop_index("ix_extraction_artifacts_job", table_name="extraction_artifacts", schema="extraction")
    op.drop_table("extraction_artifacts", schema="extraction")
    op.drop_index("ix_extraction_attempts_status", table_name="extraction_attempts", schema="extraction")
    op.drop_index("ix_extraction_attempts_job", table_name="extraction_attempts", schema="extraction")
    op.drop_table("extraction_attempts", schema="extraction")
    op.drop_index("ix_extraction_status_history_changed", table_name="extraction_job_status_history", schema="extraction")
    op.drop_index("ix_extraction_status_history_job", table_name="extraction_job_status_history", schema="extraction")
    op.drop_table("extraction_job_status_history", schema="extraction")
    op.drop_index("ix_extraction_jobs_workflow", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_created", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_status", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_template_version", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_template", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_client_competence", table_name="extraction_jobs", schema="extraction")
    op.drop_index("ix_extraction_jobs_document", table_name="extraction_jobs", schema="extraction")
    op.drop_table("extraction_jobs", schema="extraction")

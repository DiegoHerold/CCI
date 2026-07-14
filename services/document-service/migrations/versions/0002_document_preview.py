"""document preview and parsing jobs

Revision ID: 0002_document_preview
Revises: 0001_document_domain
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_document_preview"
down_revision: Union[str, None] = "0001_document_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_previews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("parser_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sheet_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text_block_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("table_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requires_ocr", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("storage_bucket", sa.String(length=128), nullable=True),
        sa.Column("storage_key", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="document",
    )
    op.create_index("ix_document_previews_document", "document_previews", ["document_id"], schema="document")
    op.create_index("ix_document_previews_status", "document_previews", ["status"], schema="document")
    op.create_index("ix_document_previews_created_at", "document_previews", ["created_at"], schema="document")

    op.create_table(
        "document_parsing_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("preview_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_by", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("parser_worker_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["preview_id"], ["document.document_previews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="document",
    )
    op.create_index("ix_document_parsing_jobs_document", "document_parsing_jobs", ["document_id"], schema="document")
    op.create_index("ix_document_parsing_jobs_status", "document_parsing_jobs", ["status"], schema="document")
    op.create_index("ix_document_parsing_jobs_created_at", "document_parsing_jobs", ["created_at"], schema="document")


def downgrade() -> None:
    op.drop_index("ix_document_parsing_jobs_created_at", table_name="document_parsing_jobs", schema="document")
    op.drop_index("ix_document_parsing_jobs_status", table_name="document_parsing_jobs", schema="document")
    op.drop_index("ix_document_parsing_jobs_document", table_name="document_parsing_jobs", schema="document")
    op.drop_table("document_parsing_jobs", schema="document")
    op.drop_index("ix_document_previews_created_at", table_name="document_previews", schema="document")
    op.drop_index("ix_document_previews_status", table_name="document_previews", schema="document")
    op.drop_index("ix_document_previews_document", table_name="document_previews", schema="document")
    op.drop_table("document_previews", schema="document")

"""document domain

Revision ID: 0001_document_domain
Revises:
Create Date: 2026-07-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_document_domain"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS document")
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("competence_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_extension", sa.String(length=16), nullable=False),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("storage_bucket", sa.String(length=128), nullable=False),
        sa.Column("storage_key", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("duplicate_of_document_id", sa.String(length=36), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("size_bytes >= 0", name="ck_documents_size_non_negative"),
        sa.ForeignKeyConstraint(
            ["duplicate_of_document_id"],
            ["document.documents.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "client_id",
            "competence_id",
            "content_hash",
            name="uq_document_client_competence_hash",
        ),
        schema="document",
    )
    op.create_index(
        "ix_document_documents_client_competence",
        "documents",
        ["client_id", "competence_id"],
        schema="document",
    )
    op.create_index("ix_document_documents_hash", "documents", ["content_hash"], schema="document")
    op.create_index("ix_document_documents_status", "documents", ["status"], schema="document")
    op.create_index("ix_document_documents_created_at", "documents", ["created_at"], schema="document")

    op.create_table(
        "document_upload_batches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("competence_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("duplicate_count", sa.Integer(), nullable=False),
        sa.Column("rejected_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="document",
    )
    op.create_index(
        "ix_document_upload_batches_client_competence",
        "document_upload_batches",
        ["client_id", "competence_id"],
        schema="document",
    )

    op.create_table(
        "document_status_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.String(length=512), nullable=True),
        sa.Column("changed_by", sa.String(length=36), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="document",
    )
    op.create_index(
        "ix_document_status_history_document_changed",
        "document_status_history",
        ["document_id", "changed_at"],
        schema="document",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_status_history_document_changed",
        table_name="document_status_history",
        schema="document",
    )
    op.drop_table("document_status_history", schema="document")
    op.drop_index(
        "ix_document_upload_batches_client_competence",
        table_name="document_upload_batches",
        schema="document",
    )
    op.drop_table("document_upload_batches", schema="document")
    op.drop_index("ix_document_documents_created_at", table_name="documents", schema="document")
    op.drop_index("ix_document_documents_status", table_name="documents", schema="document")
    op.drop_index("ix_document_documents_hash", table_name="documents", schema="document")
    op.drop_index(
        "ix_document_documents_client_competence",
        table_name="documents",
        schema="document",
    )
    op.drop_table("documents", schema="document")

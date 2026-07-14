"""template matching

Revision ID: 0002_template_matching
Revises: 0001_template_domain
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_template_matching"
down_revision: Union[str, None] = "0001_template_domain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("file_format", sa.String(length=32), nullable=False),
        sa.Column("profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("profile_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_document_profiles_document", "document_profiles", ["document_id"], schema="template")
    op.create_index("ix_template_document_profiles_format", "document_profiles", ["file_format"], schema="template")
    op.create_index("ix_template_document_profiles_created", "document_profiles", ["created_at"], schema="template")

    op.create_table(
        "template_matching_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_profile_id", sa.String(length=36), nullable=True),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("matched_template_id", sa.String(length=36), nullable=True),
        sa.Column("matched_template_version_id", sa.String(length=36), nullable=True),
        sa.Column("matched_category_id", sa.String(length=36), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("manual_override", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_profile_id"], ["template.document_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matched_category_id"], ["template.categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matched_template_id"], ["template.templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matched_template_version_id"], ["template.template_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_matching_runs_document", "template_matching_runs", ["document_id"], schema="template")
    op.create_index("ix_template_matching_runs_status", "template_matching_runs", ["status"], schema="template")
    op.create_index("ix_template_matching_runs_template", "template_matching_runs", ["matched_template_id"], schema="template")
    op.create_index("ix_template_matching_runs_created", "template_matching_runs", ["created_at"], schema="template")

    op.create_table(
        "template_matching_candidates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("matching_run_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("template_version_id", sa.String(length=36), nullable=True),
        sa.Column("category_id", sa.String(length=36), nullable=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("matched_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_required_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("negative_matches", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("score_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["template.categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["matching_run_id"], ["template.template_matching_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["template.templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_version_id"], ["template.template_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        schema="template",
    )
    op.create_index("ix_template_matching_candidates_run", "template_matching_candidates", ["matching_run_id"], schema="template")
    op.create_index("ix_template_matching_candidates_template", "template_matching_candidates", ["template_id"], schema="template")
    op.create_index("ix_template_matching_candidates_score", "template_matching_candidates", ["score"], schema="template")
    op.create_index("ix_template_matching_candidates_rank", "template_matching_candidates", ["rank_position"], schema="template")


def downgrade() -> None:
    op.drop_index("ix_template_matching_candidates_rank", table_name="template_matching_candidates", schema="template")
    op.drop_index("ix_template_matching_candidates_score", table_name="template_matching_candidates", schema="template")
    op.drop_index("ix_template_matching_candidates_template", table_name="template_matching_candidates", schema="template")
    op.drop_index("ix_template_matching_candidates_run", table_name="template_matching_candidates", schema="template")
    op.drop_table("template_matching_candidates", schema="template")
    op.drop_index("ix_template_matching_runs_created", table_name="template_matching_runs", schema="template")
    op.drop_index("ix_template_matching_runs_template", table_name="template_matching_runs", schema="template")
    op.drop_index("ix_template_matching_runs_status", table_name="template_matching_runs", schema="template")
    op.drop_index("ix_template_matching_runs_document", table_name="template_matching_runs", schema="template")
    op.drop_table("template_matching_runs", schema="template")
    op.drop_index("ix_template_document_profiles_created", table_name="document_profiles", schema="template")
    op.drop_index("ix_template_document_profiles_format", table_name="document_profiles", schema="template")
    op.drop_index("ix_template_document_profiles_document", table_name="document_profiles", schema="template")
    op.drop_table("document_profiles", schema="template")

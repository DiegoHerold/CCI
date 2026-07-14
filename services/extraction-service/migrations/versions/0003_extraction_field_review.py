"""extraction field review

Revision ID: 0003_extraction_field_review
Revises: 0002_extraction_results
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_extraction_field_review"
down_revision: Union[str, None] = "0002_extraction_results"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "extracted_field_reviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("extraction_result_id", sa.String(length=36), nullable=False),
        sa.Column("field_value_id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("previous_status", sa.String(length=32), nullable=False),
        sa.Column("previous_raw_value", sa.JSON(), nullable=True),
        sa.Column("previous_normalized_value", sa.Text(), nullable=True),
        sa.Column("previous_display_value", sa.Text(), nullable=True),
        sa.Column("previous_normalized_json", sa.JSON(), nullable=True),
        sa.Column("new_raw_value", sa.JSON(), nullable=True),
        sa.Column("new_normalized_value", sa.Text(), nullable=True),
        sa.Column("new_display_value", sa.Text(), nullable=True),
        sa.Column("new_normalized_json", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("reviewed_by", sa.String(length=128), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["extraction_result_id"], ["extraction.extraction_results.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["field_value_id"], ["extraction.extracted_field_values.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="extraction",
    )
    op.create_index("ix_extracted_field_reviews_field", "extracted_field_reviews", ["field_value_id"], schema="extraction")
    op.create_index("ix_extracted_field_reviews_result", "extracted_field_reviews", ["extraction_result_id"], schema="extraction")
    op.create_index("ix_extracted_field_reviews_action", "extracted_field_reviews", ["action"], schema="extraction")


def downgrade() -> None:
    op.drop_index("ix_extracted_field_reviews_action", table_name="extracted_field_reviews", schema="extraction")
    op.drop_index("ix_extracted_field_reviews_result", table_name="extracted_field_reviews", schema="extraction")
    op.drop_index("ix_extracted_field_reviews_field", table_name="extracted_field_reviews", schema="extraction")
    op.drop_table("extracted_field_reviews", schema="extraction")

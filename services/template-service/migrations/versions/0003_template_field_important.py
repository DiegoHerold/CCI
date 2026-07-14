"""template field important flag

Revision ID: 0003_template_field_important
Revises: 0002_template_matching
Create Date: 2026-07-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_template_field_important"
down_revision: Union[str, None] = "0002_template_matching"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "template_fields",
        sa.Column("important", sa.Boolean(), nullable=False, server_default=sa.false()),
        schema="template",
    )
    op.alter_column("template_fields", "important", server_default=None, schema="template")


def downgrade() -> None:
    op.drop_column("template_fields", "important", schema="template")

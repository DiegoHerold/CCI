"""Backfill creator bindings for existing clients.

Revision ID: 0002_creator_bindings
Revises: 0001_client_domain
Create Date: 2026-07-14
"""

from alembic import op


revision = "0002_creator_bindings"
down_revision = "0001_client_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO core.client_users (
            id,
            client_id,
            user_id,
            client_role,
            status,
            is_primary_responsible,
            responsibility_area
        )
        SELECT
            c.id,
            c.id,
            c.created_by_user_id,
            'CLIENT_MANAGER',
            'ACTIVE',
            true,
            'GENERAL'
        FROM core.clients c
        WHERE NOT EXISTS (
            SELECT 1
            FROM core.client_users cu
            WHERE cu.client_id = c.id
              AND cu.user_id = c.created_by_user_id
        )
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM core.client_users cu
        USING core.clients c
        WHERE cu.id = c.id
          AND cu.client_id = c.id
          AND cu.user_id = c.created_by_user_id
          AND cu.client_role = 'CLIENT_MANAGER'
          AND cu.responsibility_area = 'GENERAL'
        """
    )

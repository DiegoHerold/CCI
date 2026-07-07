"""Create Identity schema and RBAC tables.

Revision ID: 0001_identity
Revises:
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_identity"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.create_table(
        "roles",
        sa.Column("name", sa.String(length=32), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("name"),
        schema="auth",
    )
    op.create_table(
        "permissions",
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("name"),
        schema="auth",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_auth_users_email"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_users_status", "users", ["status"], schema="auth"
    )
    op.create_table(
        "role_permissions",
        sa.Column("role_name", sa.String(length=32), nullable=False),
        sa.Column("permission_name", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_name"], ["auth.permissions.name"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_name"], ["auth.roles.name"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_name", "permission_name"),
        schema="auth",
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("role_name", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_name"], ["auth.roles.name"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["auth.users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "role_name"),
        schema="auth",
    )


def downgrade() -> None:
    op.drop_table("user_roles", schema="auth")
    op.drop_table("role_permissions", schema="auth")
    op.drop_index("ix_auth_users_status", table_name="users", schema="auth")
    op.drop_table("users", schema="auth")
    op.drop_table("permissions", schema="auth")
    op.drop_table("roles", schema="auth")

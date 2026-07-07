"""Add sessions, login protection and identity audit.

Revision ID: 0002_identity_hardening
Revises: 0001_identity
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_identity_hardening"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        schema="auth",
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        schema="auth",
    )
    op.add_column(
        "users",
        sa.Column("last_failed_login_at", sa.DateTime(timezone=True), nullable=True),
        schema="auth",
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["user_id"], ["auth.users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "refresh_token_hash", name="uq_auth_sessions_refresh_token_hash"
        ),
        schema="auth",
    )
    op.create_index(
        "ix_auth_sessions_user_id", "sessions", ["user_id"], schema="auth"
    )
    op.create_index(
        "ix_auth_sessions_expires_at", "sessions", ["expires_at"], schema="auth"
    )
    op.create_index(
        "ix_auth_sessions_revoked_at", "sessions", ["revoked_at"], schema="auth"
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["auth.users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="auth",
    )
    op.create_index(
        "ix_auth_audit_events_user_id", "audit_events", ["user_id"], schema="auth"
    )
    op.create_index(
        "ix_auth_audit_events_event_type",
        "audit_events",
        ["event_type"],
        schema="auth",
    )

    op.create_table(
        "login_rate_limits",
        sa.Column("identifier_hash", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("identifier_hash"),
        schema="auth",
    )


def downgrade() -> None:
    op.drop_table("login_rate_limits", schema="auth")
    op.drop_index(
        "ix_auth_audit_events_event_type",
        table_name="audit_events",
        schema="auth",
    )
    op.drop_index(
        "ix_auth_audit_events_user_id",
        table_name="audit_events",
        schema="auth",
    )
    op.drop_table("audit_events", schema="auth")
    op.drop_index(
        "ix_auth_sessions_revoked_at", table_name="sessions", schema="auth"
    )
    op.drop_index(
        "ix_auth_sessions_expires_at", table_name="sessions", schema="auth"
    )
    op.drop_index(
        "ix_auth_sessions_user_id", table_name="sessions", schema="auth"
    )
    op.drop_table("sessions", schema="auth")
    op.drop_column("users", "last_failed_login_at", schema="auth")
    op.drop_column("users", "locked_until", schema="auth")
    op.drop_column("users", "failed_login_attempts", schema="auth")

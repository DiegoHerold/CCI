"""Create Client Service domain tables.

Revision ID: 0001_client_domain
Revises:
Create Date: 2026-07-07
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_client_domain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.create_table(
        "clients",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("code", sa.String(64), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trade_name", sa.String(255), nullable=True),
        sa.Column("cnpj", sa.String(18), nullable=False),
        sa.Column("cnpj_normalized", sa.String(14), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("tax_regime", sa.String(32), nullable=True),
        sa.Column("state_registration", sa.String(64), nullable=True),
        sa.Column("municipal_registration", sa.String(64), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("default_folder_path", sa.String(1024), nullable=True),
        sa.Column("competence_folder_pattern", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("cnpj_normalized ~ '^[0-9]{14}$'", name="ck_clients_cnpj_digits"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cnpj_normalized", name="uq_core_clients_cnpj_normalized"),
        sa.UniqueConstraint("code", name="uq_core_clients_code"),
        schema="core",
    )
    op.create_index("ix_core_clients_name", "clients", ["name"], schema="core")
    op.create_index("ix_core_clients_status", "clients", ["status"], schema="core")

    op.create_table(
        "client_competencies",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("client_id", sa.String(36), nullable=False),
        sa.Column("period", sa.String(7), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("folder_path", sa.String(1024), nullable=True),
        sa.Column("folder_resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", sa.String(36), nullable=False),
        sa.Column("closed_by_user_id", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="ck_client_competencies_month"),
        sa.CheckConstraint("year >= 1900 AND year <= 2200", name="ck_client_competencies_year"),
        sa.ForeignKeyConstraint(["client_id"], ["core.clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "period", name="uq_client_competencies_client_period"),
        schema="core",
    )
    op.create_index("ix_core_client_competencies_client_id", "client_competencies", ["client_id"], schema="core")
    op.create_index("ix_core_client_competencies_period", "client_competencies", ["period"], schema="core")
    op.create_index("ix_core_client_competencies_status", "client_competencies", ["status"], schema="core")

    op.create_table(
        "client_users",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("client_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("client_role", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("is_primary_responsible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("responsibility_area", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["client_id"], ["core.clients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_id", "user_id", name="uq_client_users_client_user"),
        schema="core",
    )
    op.create_index("ix_core_client_users_client_id", "client_users", ["client_id"], schema="core")
    op.create_index("ix_core_client_users_user_id", "client_users", ["user_id"], schema="core")
    op.create_index("ix_core_client_users_status", "client_users", ["status"], schema="core")

    op.create_table(
        "user_client_preferences",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("default_client_id", sa.String(36), nullable=True),
        sa.Column("default_competence_period", sa.String(7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["default_client_id"], ["core.clients.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_core_user_client_preferences_user_id"),
        schema="core",
    )

    op.create_table(
        "client_audit_events",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("client_id", sa.String(36), nullable=True),
        sa.Column("competency_id", sa.String(36), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="core",
    )
    op.create_index("ix_core_client_audit_events_event_type", "client_audit_events", ["event_type"], schema="core")
    op.create_index("ix_core_client_audit_events_user_id", "client_audit_events", ["user_id"], schema="core")
    op.create_index("ix_core_client_audit_events_client_created", "client_audit_events", ["client_id", "created_at"], schema="core")


def downgrade() -> None:
    op.drop_table("client_audit_events", schema="core")
    op.drop_table("user_client_preferences", schema="core")
    op.drop_table("client_users", schema="core")
    op.drop_table("client_competencies", schema="core")
    op.drop_table("clients", schema="core")

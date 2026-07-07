from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


def new_id() -> str:
    return str(uuid4())


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (
        CheckConstraint("cnpj_normalized ~ '^[0-9]{14}$'", name="ck_clients_cnpj_digits"),
        {"schema": "core"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    trade_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False)
    cnpj_normalized: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    tax_regime: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state_registration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    municipal_registration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    default_folder_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    competence_folder_pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    competencies: Mapped[list["ClientCompetency"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    users: Mapped[list["ClientUser"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class ClientCompetency(Base):
    __tablename__ = "client_competencies"
    __table_args__ = (
        UniqueConstraint("client_id", "period", name="uq_client_competencies_client_period"),
        CheckConstraint("month >= 1 AND month <= 12", name="ck_client_competencies_month"),
        CheckConstraint("year >= 1900 AND year <= 2200", name="ck_client_competencies_year"),
        {"schema": "core"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("core.clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    folder_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    folder_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    closed_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client: Mapped[Client] = relationship(back_populates="competencies")


class ClientUser(Base):
    __tablename__ = "client_users"
    __table_args__ = (
        UniqueConstraint("client_id", "user_id", name="uq_client_users_client_user"),
        {"schema": "core"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    client_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("core.clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    client_role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_primary_responsible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    responsibility_area: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client: Mapped[Client] = relationship(back_populates="users")


class UserClientPreference(Base):
    __tablename__ = "user_client_preferences"
    __table_args__ = ({"schema": "core"},)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)
    default_client_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("core.clients.id", ondelete="SET NULL"), nullable=True
    )
    default_competence_period: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ClientAuditEvent(Base):
    __tablename__ = "client_audit_events"
    __table_args__ = (
        Index("ix_core_client_audit_events_client_created", "client_id", "created_at"),
        {"schema": "core"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    client_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    competency_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

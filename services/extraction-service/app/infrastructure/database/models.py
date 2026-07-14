from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


def new_id() -> str:
    return str(uuid4())


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"
    __table_args__ = (
        Index("ix_extraction_jobs_document", "document_id"),
        Index("ix_extraction_jobs_client_competence", "client_id", "competence_id"),
        Index("ix_extraction_jobs_template", "template_id"),
        Index("ix_extraction_jobs_template_version", "template_version_id"),
        Index("ix_extraction_jobs_status", "status"),
        Index("ix_extraction_jobs_created", "created_at"),
        Index("ix_extraction_jobs_workflow", "workflow_id"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), nullable=False)
    competence_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    matching_run_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_by: Mapped[str] = mapped_column(String(128), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    history: Mapped[list["ExtractionJobStatusHistory"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="ExtractionJobStatusHistory.changed_at"
    )
    attempts: Mapped[list["ExtractionAttempt"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="ExtractionAttempt.attempt_number"
    )
    artifacts: Mapped[list["ExtractionArtifact"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="ExtractionArtifact.created_at"
    )


class ExtractionJobStatusHistory(Base):
    __tablename__ = "extraction_job_status_history"
    __table_args__ = (
        Index("ix_extraction_status_history_job", "extraction_job_id"),
        Index("ix_extraction_status_history_changed", "changed_at"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_jobs.id", ondelete="CASCADE"), nullable=False
    )
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    job: Mapped[ExtractionJob] = relationship(back_populates="history")


class ExtractionAttempt(Base):
    __tablename__ = "extraction_attempts"
    __table_args__ = (
        Index("ix_extraction_attempts_job", "extraction_job_id"),
        Index("ix_extraction_attempts_status", "status"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_jobs.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    worker_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    worker_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[ExtractionJob] = relationship(back_populates="attempts")


class ExtractionArtifact(Base):
    __tablename__ = "extraction_artifacts"
    __table_args__ = (
        Index("ix_extraction_artifacts_job", "extraction_job_id"),
        Index("ix_extraction_artifacts_document", "document_id"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_jobs.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[ExtractionJob] = relationship(back_populates="artifacts")

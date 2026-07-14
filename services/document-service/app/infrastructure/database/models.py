from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


def new_id() -> str:
    return str(uuid4())


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint(
            "client_id",
            "competence_id",
            "content_hash",
            name="uq_document_client_competence_hash",
        ),
        CheckConstraint("size_bytes >= 0", name="ck_documents_size_non_negative"),
        Index("ix_document_documents_client_competence", "client_id", "competence_id"),
        Index("ix_document_documents_hash", "content_hash"),
        Index("ix_document_documents_status", "status"),
        Index("ix_document_documents_created_at", "created_at"),
        {"schema": "document"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    client_id: Mapped[str] = mapped_column(String(36), nullable=False)
    competence_id: Mapped[str] = mapped_column(String(36), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_extension: Mapped[str] = mapped_column(String(16), nullable=False)
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    duplicate_of_document_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("document.documents.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    duplicate_of: Mapped["Document | None"] = relationship(remote_side=[id])


class DocumentPreview(Base):
    __tablename__ = "document_previews"
    __table_args__ = (
        Index("ix_document_previews_document", "document_id"),
        Index("ix_document_previews_status", "status"),
        Index("ix_document_previews_created_at", "created_at"),
        {"schema": "document"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document.documents.id", ondelete="CASCADE"), nullable=False
    )
    file_format: Mapped[str] = mapped_column(String(32), nullable=False)
    parser_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sheet_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text_block_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    table_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    storage_bucket: Mapped[str | None] = mapped_column(String(128), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    document: Mapped[Document] = relationship()


class DocumentParsingJob(Base):
    __tablename__ = "document_parsing_jobs"
    __table_args__ = (
        Index("ix_document_parsing_jobs_document", "document_id"),
        Index("ix_document_parsing_jobs_status", "status"),
        Index("ix_document_parsing_jobs_created_at", "created_at"),
        {"schema": "document"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document.documents.id", ondelete="CASCADE"), nullable=False
    )
    preview_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document.document_previews.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    requested_by: Mapped[str] = mapped_column(String(36), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parser_worker_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    document: Mapped[Document] = relationship()
    preview: Mapped[DocumentPreview] = relationship()


class DocumentUploadBatch(Base):
    __tablename__ = "document_upload_batches"
    __table_args__ = (
        Index("ix_document_upload_batches_client_competence", "client_id", "competence_id"),
        {"schema": "document"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    client_id: Mapped[str] = mapped_column(String(36), nullable=False)
    competence_id: Mapped[str] = mapped_column(String(36), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_by: Mapped[str] = mapped_column(String(36), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DocumentStatusHistory(Base):
    __tablename__ = "document_status_history"
    __table_args__ = (
        Index("ix_document_status_history_document_changed", "document_id", "changed_at"),
        {"schema": "document"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("document.documents.id", ondelete="CASCADE"), nullable=False
    )
    previous_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    changed_by: Mapped[str] = mapped_column(String(36), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

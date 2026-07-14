from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, func
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
    results: Mapped[list["ExtractionResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="ExtractionResult.created_at"
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


class ExtractionResult(Base):
    __tablename__ = "extraction_results"
    __table_args__ = (
        Index("ix_extraction_results_job", "extraction_job_id"),
        Index("ix_extraction_results_document", "document_id"),
        Index("ix_extraction_results_client_competence", "client_id", "competence_id"),
        Index("ix_extraction_results_template", "template_id"),
        Index("ix_extraction_results_template_version", "template_version_id"),
        Index("ix_extraction_results_status", "status"),
        Index("ix_extraction_results_created", "created_at"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_jobs.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    client_id: Mapped[str] = mapped_column(String(36), nullable=False)
    competence_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    field_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    normalized_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    warning_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[ExtractionJob] = relationship(back_populates="results")
    objects: Mapped[list["ExtractedObject"]] = relationship(
        back_populates="result", cascade="all, delete-orphan", order_by="ExtractedObject.created_at"
    )
    fields: Mapped[list["ExtractedFieldValue"]] = relationship(
        back_populates="result", cascade="all, delete-orphan", order_by="ExtractedFieldValue.created_at"
    )
    array_items: Mapped[list["ExtractedArrayItem"]] = relationship(
        back_populates="result", cascade="all, delete-orphan", order_by="ExtractedArrayItem.item_index"
    )
    evidences: Mapped[list["ExtractionEvidence"]] = relationship(
        back_populates="result", cascade="all, delete-orphan", order_by="ExtractionEvidence.created_at"
    )


class ExtractedObject(Base):
    __tablename__ = "extracted_objects"
    __table_args__ = (
        Index("ix_extracted_objects_result", "extraction_result_id"),
        Index("ix_extracted_objects_parent", "parent_object_id"),
        Index("ix_extracted_objects_path", "field_path"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="CASCADE"), nullable=False
    )
    parent_object_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("extraction.extracted_objects.id", ondelete="SET NULL"), nullable=True
    )
    field_path: Mapped[str] = mapped_column(String(512), nullable=False)
    field_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    item_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    result: Mapped[ExtractionResult] = relationship(back_populates="objects")


class ExtractedArrayItem(Base):
    __tablename__ = "extracted_array_items"
    __table_args__ = (
        Index("ix_extracted_array_items_result", "extraction_result_id"),
        Index("ix_extracted_array_items_path", "array_field_path"),
        Index("ix_extracted_array_items_result_path_index", "extraction_result_id", "array_field_path", "item_index"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="CASCADE"), nullable=False
    )
    array_field_path: Mapped[str] = mapped_column(String(512), nullable=False)
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    result: Mapped[ExtractionResult] = relationship(back_populates="array_items")


class ExtractedFieldValue(Base):
    __tablename__ = "extracted_field_values"
    __table_args__ = (
        Index("ix_extracted_field_values_result", "extraction_result_id"),
        Index("ix_extracted_field_values_path", "field_path"),
        Index("ix_extracted_field_values_field", "field_id"),
        Index("ix_extracted_field_values_status", "status"),
        Index("ix_extracted_field_values_confidence", "confidence"),
        Index("ix_extracted_field_values_item", "item_index"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="CASCADE"), nullable=False
    )
    extracted_object_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("extraction.extracted_objects.id", ondelete="SET NULL"), nullable=True
    )
    field_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    field_path: Mapped[str] = mapped_column(String(512), nullable=False)
    field_type: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    item_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    result: Mapped[ExtractionResult] = relationship(back_populates="fields")


class ExtractedFieldReview(Base):
    __tablename__ = "extracted_field_reviews"
    __table_args__ = (
        Index("ix_extracted_field_reviews_field", "field_value_id"),
        Index("ix_extracted_field_reviews_result", "extraction_result_id"),
        Index("ix_extracted_field_reviews_action", "action"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="CASCADE"), nullable=False
    )
    field_value_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extracted_field_values.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_raw_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    previous_normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_display_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    previous_normalized_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    new_raw_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    new_normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_display_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_normalized_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str] = mapped_column(String(128), nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ExtractionEvidence(Base):
    __tablename__ = "extraction_evidences"
    __table_args__ = (
        Index("ix_extraction_evidences_result", "extraction_result_id"),
        Index("ix_extraction_evidences_document", "document_id"),
        Index("ix_extraction_evidences_field", "field_value_id"),
        Index("ix_extraction_evidences_type", "evidence_type"),
        Index("ix_extraction_evidences_rule", "rule_id"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_result_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    field_value_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("extraction.extracted_field_values.id", ondelete="SET NULL"), nullable=True
    )
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_json: Mapped[object | None] = mapped_column(JSON, nullable=True)
    sheet_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cell_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_value: Mapped[object | None] = mapped_column(JSON, nullable=True)
    rule_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rule_strategy: Mapped[str | None] = mapped_column(String(128), nullable=True)
    template_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    result: Mapped[ExtractionResult] = relationship(back_populates="evidences")


class NormalizationRun(Base):
    __tablename__ = "normalization_runs"
    __table_args__ = (
        Index("ix_normalization_runs_job", "extraction_job_id"),
        Index("ix_normalization_runs_result", "extraction_result_id"),
        Index("ix_normalization_runs_status", "status"),
        {"schema": "extraction"},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    extraction_job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("extraction.extraction_jobs.id", ondelete="CASCADE"), nullable=False
    )
    extraction_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("extraction.extraction_results.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

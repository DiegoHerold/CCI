from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DocumentStatus, FileFormat, ParsingJobStatus
from app.infrastructure.database.models import Document, DocumentParsingJob, DocumentPreview, DocumentUploadBatch


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
        from_attributes=True,
    )


class DocumentResponse(ApiModel):
    document_id: str
    client_id: str
    competence_id: str
    original_filename: str
    stored_filename: str | None = None
    file_extension: str | None = None
    file_format: FileFormat
    mime_type: str | None = None
    size_bytes: int | None = None
    content_hash: str
    storage_bucket: str | None = None
    storage_key: str | None = None
    status: DocumentStatus
    is_duplicate: bool = False
    duplicate_of_document_id: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, entity: Document) -> "DocumentResponse":
        return cls(
            document_id=entity.id,
            client_id=entity.client_id,
            competence_id=entity.competence_id,
            original_filename=entity.original_filename,
            stored_filename=entity.stored_filename,
            file_extension=entity.file_extension,
            file_format=FileFormat(entity.file_format),
            mime_type=entity.mime_type,
            size_bytes=entity.size_bytes,
            content_hash=entity.content_hash,
            storage_bucket=entity.storage_bucket,
            storage_key=entity.storage_key,
            status=DocumentStatus(entity.status),
            is_duplicate=False,
            duplicate_of_document_id=entity.duplicate_of_document_id,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    @classmethod
    def duplicate(cls, entity: Document) -> "DocumentResponse":
        return cls(
            document_id=entity.id,
            client_id=entity.client_id,
            competence_id=entity.competence_id,
            original_filename=entity.original_filename,
            stored_filename=entity.stored_filename,
            file_extension=entity.file_extension,
            file_format=FileFormat(entity.file_format),
            mime_type=entity.mime_type,
            size_bytes=entity.size_bytes,
            content_hash=entity.content_hash,
            storage_bucket=entity.storage_bucket,
            storage_key=entity.storage_key,
            status=DocumentStatus.DUPLICATE,
            is_duplicate=True,
            duplicate_of_document_id=entity.id,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class DocumentListResponse(ApiModel):
    items: list[DocumentResponse]
    page: int
    limit: int
    total: int


class DocumentStatusUpdate(ApiModel):
    status: DocumentStatus
    reason: str | None = Field(default=None, max_length=512)


class ZipError(ApiModel):
    filename: str
    reason: str


class ZipDocumentItem(ApiModel):
    document_id: str
    original_filename: str
    status: DocumentStatus
    is_duplicate: bool
    duplicate_of_document_id: str | None = None

    @classmethod
    def from_document(cls, response: DocumentResponse) -> "ZipDocumentItem":
        return cls(
            document_id=response.document_id,
            original_filename=response.original_filename,
            status=response.status,
            is_duplicate=response.is_duplicate,
            duplicate_of_document_id=response.duplicate_of_document_id,
        )


class UploadZipResponse(ApiModel):
    batch_id: str
    client_id: str
    competence_id: str
    total_files: int
    created: int
    duplicates: int
    rejected: int
    documents: list[ZipDocumentItem]
    errors: list[ZipError]

    @classmethod
    def from_batch(
        cls,
        batch: DocumentUploadBatch,
        documents: list[DocumentResponse],
        errors: list[ZipError],
    ) -> "UploadZipResponse":
        return cls(
            batch_id=batch.id,
            client_id=batch.client_id,
            competence_id=batch.competence_id,
            total_files=batch.total_files,
            created=batch.created_count,
            duplicates=batch.duplicate_count,
            rejected=batch.rejected_count,
            documents=[ZipDocumentItem.from_document(item) for item in documents],
            errors=errors,
        )


class PreviewRequestResponse(ApiModel):
    document_id: str
    parsing_job_id: str
    status: DocumentStatus


class DocumentPreviewStatusResponse(ApiModel):
    document_id: str
    status: DocumentStatus
    parsing_job_id: str | None = None
    preview_id: str | None = None
    error_message: str | None = None


class DocumentPreviewMetadataResponse(ApiModel):
    preview_id: str
    document_id: str
    file_format: FileFormat
    parser_version: str | None = None
    status: DocumentStatus
    page_count: int = 0
    sheet_count: int = 0
    text_block_count: int = 0
    table_count: int = 0
    requires_ocr: bool = False
    storage_bucket: str | None = None
    storage_key: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_entity(cls, preview: DocumentPreview) -> "DocumentPreviewMetadataResponse":
        return cls(
            preview_id=preview.id,
            document_id=preview.document_id,
            file_format=FileFormat(preview.file_format),
            parser_version=preview.parser_version,
            status=DocumentStatus(preview.status),
            page_count=preview.page_count,
            sheet_count=preview.sheet_count,
            text_block_count=preview.text_block_count,
            table_count=preview.table_count,
            requires_ocr=preview.requires_ocr,
            storage_bucket=preview.storage_bucket,
            storage_key=preview.storage_key,
            error_message=preview.error_message,
            created_at=preview.created_at,
            updated_at=preview.updated_at,
        )


class DocumentPreviewResponse(ApiModel):
    document_id: str
    status: DocumentStatus
    preview: dict[str, Any] | None = None
    metadata: DocumentPreviewMetadataResponse | None = None
    error_message: str | None = None


class ParsingJobResponse(ApiModel):
    parsing_job_id: str
    document_id: str
    preview_id: str
    status: ParsingJobStatus
    requested_by: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    parser_worker_version: str | None = None

    @classmethod
    def from_entity(cls, job: DocumentParsingJob) -> "ParsingJobResponse":
        return cls(
            parsing_job_id=job.id,
            document_id=job.document_id,
            preview_id=job.preview_id,
            status=ParsingJobStatus(job.status),
            requested_by=job.requested_by,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
            parser_worker_version=job.parser_worker_version,
        )

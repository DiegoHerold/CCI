from enum import StrEnum


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    STORAGE_FAILED = "storage_failed"
    PREVIEW_PENDING = "preview_pending"
    PREVIEW_PROCESSING = "preview_processing"
    PREVIEW_READY = "preview_ready"
    PREVIEW_FAILED = "preview_failed"
    TEMPLATE_PENDING = "template_pending"
    TEMPLATE_MATCHED = "template_matched"
    TEMPLATE_NOT_FOUND = "template_not_found"
    EXTRACTION_PENDING = "extraction_pending"
    EXTRACTION_RUNNING = "extraction_running"
    EXTRACTED = "extracted"
    EXTRACTION_FAILED = "extraction_failed"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    FAILED = "failed"


class FileFormat(StrEnum):
    PDF = "PDF"
    EXCEL = "EXCEL"
    CSV = "CSV"
    TXT = "TXT"
    DOCX = "DOCX"
    XML = "XML"
    ZIP = "ZIP"


class UploadBatchStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    REJECTED = "rejected"


class ParsingJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


EXTENSION_FORMATS: dict[str, FileFormat] = {
    ".pdf": FileFormat.PDF,
    ".xlsx": FileFormat.EXCEL,
    ".xls": FileFormat.EXCEL,
    ".csv": FileFormat.CSV,
    ".txt": FileFormat.TXT,
    ".docx": FileFormat.DOCX,
    ".xml": FileFormat.XML,
    ".zip": FileFormat.ZIP,
}


MIME_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xml": "application/xml",
    ".zip": "application/zip",
}

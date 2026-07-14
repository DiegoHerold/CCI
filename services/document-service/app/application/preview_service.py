import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.application.context import RequestContext
from app.application.schemas import (
    DocumentPreviewResponse,
    DocumentPreviewStatusResponse,
    PreviewRequestResponse,
)
from app.config import Settings
from app.domain.enums import DocumentStatus, ParsingJobStatus
from app.errors import BusinessRuleError, NotFoundError
from app.infrastructure.database.models import (
    Document,
    DocumentParsingJob,
    DocumentPreview,
    DocumentStatusHistory,
    new_id,
)
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.parser_worker import (
    ParserWorkerClient,
    ParserWorkerParseRequest,
)
from app.infrastructure.repositories import (
    DocumentRepository,
    ParsingJobRepository,
    PreviewRepository,
    StatusHistoryRepository,
)
from app.infrastructure.storage import StorageClient


class PreviewService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        storage: StorageClient,
        publisher: EventPublisher,
        parser_worker: ParserWorkerClient,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage
        self.publisher = publisher
        self.parser_worker = parser_worker
        self.documents = DocumentRepository(session)
        self.previews = PreviewRepository(session)
        self.jobs = ParsingJobRepository(session)
        self.status_history = StatusHistoryRepository(session)

    def create_preview_job(
        self,
        document_id: str,
        actor: Principal,
        context: RequestContext,
    ) -> PreviewRequestResponse:
        document = self._get_document(document_id)
        if document.size_bytes > self.settings.parser_max_file_size_bytes:
            raise BusinessRuleError("FILE_TOO_LARGE_FOR_PREVIEW", "File exceeds parser size limit")

        preview_id = new_id()
        preview_key = (
            f"clients/{document.client_id}/competences/{document.competence_id}/"
            f"documents/{document.id}/preview/{preview_id}.json"
        )
        preview = DocumentPreview(
            id=preview_id,
            document_id=document.id,
            file_format=document.file_format,
            status=DocumentStatus.PREVIEW_PENDING.value,
            storage_bucket=self.settings.minio_bucket_documents_preview,
            storage_key=preview_key,
        )
        job = DocumentParsingJob(
            document_id=document.id,
            preview_id=preview.id,
            status=ParsingJobStatus.PENDING.value,
            requested_by=actor.id,
        )
        self.previews.add(preview)
        self.jobs.add(job)
        self._set_document_status(
            document,
            DocumentStatus.PREVIEW_PENDING,
            "preview_requested",
            actor.id,
        )
        self.session.commit()
        self._publish(
            "DocumentPreviewRequested",
            context,
            document,
            preview_id=preview.id,
            parsing_job_id=job.id,
        )
        return PreviewRequestResponse(
            document_id=document.id,
            parsing_job_id=job.id,
            status=DocumentStatus.PREVIEW_PENDING,
        )

    async def process_job(
        self,
        parsing_job_id: str,
        actor: Principal,
        context: RequestContext,
    ) -> None:
        job = self.jobs.get(parsing_job_id)
        if job is None:
            raise NotFoundError("Parsing job")
        document = self._get_document(job.document_id)
        preview = self.previews.get(job.preview_id)
        if preview is None:
            raise NotFoundError("Document preview")

        now = datetime.now(timezone.utc)
        job.status = ParsingJobStatus.PROCESSING.value
        job.started_at = now
        preview.status = DocumentStatus.PREVIEW_PROCESSING.value
        self._set_document_status(
            document,
            DocumentStatus.PREVIEW_PROCESSING,
            "preview_processing",
            actor.id,
        )
        self.session.commit()
        self._publish(
            "DocumentPreviewStarted",
            context,
            document,
            preview_id=preview.id,
            parsing_job_id=job.id,
        )

        try:
            result = await self.parser_worker.parse(
                ParserWorkerParseRequest(
                    document_id=document.id,
                    client_id=document.client_id,
                    competence_id=document.competence_id,
                    file_format=document.file_format,
                    original_filename=document.original_filename,
                    storage_bucket=document.storage_bucket,
                    storage_key=document.storage_key,
                    preview_bucket=preview.storage_bucket or self.settings.minio_bucket_documents_preview,
                    preview_storage_key=preview.storage_key or "",
                    max_file_size_bytes=self.settings.parser_max_file_size_bytes,
                    max_preview_json_size_bytes=self.settings.parser_preview_max_json_size_bytes,
                )
            )
        except Exception as exc:
            self.session.rollback()
            self._mark_failed(job.id, preview.id, document.id, actor.id, context, str(exc))
            return

        job.status = ParsingJobStatus.COMPLETED.value
        job.finished_at = datetime.now(timezone.utc)
        job.parser_worker_version = result.parser_version
        preview.status = DocumentStatus.PREVIEW_READY.value
        preview.parser_version = result.parser_version
        preview.storage_bucket = result.storage_bucket
        preview.storage_key = result.storage_key
        preview.page_count = result.page_count
        preview.sheet_count = result.sheet_count
        preview.text_block_count = result.text_block_count
        preview.table_count = result.table_count
        preview.requires_ocr = result.requires_ocr
        preview.error_message = None
        self._set_document_status(
            document,
            DocumentStatus.PREVIEW_READY,
            "preview_generated",
            actor.id,
        )
        self.session.commit()
        self._publish(
            "DocumentPreviewGenerated",
            context,
            document,
            preview_id=preview.id,
            parsing_job_id=job.id,
            parser_version=result.parser_version,
            storage_bucket=result.storage_bucket,
            storage_key=result.storage_key,
            file_format=result.file_format,
        )

    def get_status(self, document_id: str) -> DocumentPreviewStatusResponse:
        document = self._get_document(document_id)
        job = self.jobs.latest_for_document(document.id)
        preview = self.previews.latest_for_document(document.id)
        status = DocumentStatus(preview.status if preview else document.status)
        return DocumentPreviewStatusResponse(
            document_id=document.id,
            status=status,
            parsing_job_id=job.id if job else None,
            preview_id=preview.id if preview else None,
            error_message=(preview.error_message if preview else None) or (job.error_message if job else None),
        )

    def get_preview(self, document_id: str) -> DocumentPreviewResponse:
        document = self._get_document(document_id)
        preview = self.previews.latest_for_document(document.id)
        if preview is None:
            raise NotFoundError("Document preview")

        payload = None
        if preview.status == DocumentStatus.PREVIEW_READY.value and preview.storage_bucket and preview.storage_key:
            raw = self.storage.download_bytes(bucket=preview.storage_bucket, key=preview.storage_key)
            payload = json.loads(raw.decode("utf-8"))
        return DocumentPreviewResponse(
            document_id=document.id,
            status=DocumentStatus(preview.status),
            preview=payload,
            metadata=None,
            error_message=preview.error_message,
        )

    def _mark_failed(
        self,
        parsing_job_id: str,
        preview_id: str,
        document_id: str,
        actor_id: str,
        context: RequestContext,
        error_message: str,
    ) -> None:
        job = self.jobs.get(parsing_job_id)
        preview = self.previews.get(preview_id)
        document = self._get_document(document_id)
        if job is not None:
            job.status = ParsingJobStatus.FAILED.value
            job.finished_at = datetime.now(timezone.utc)
            job.error_message = error_message[:1024]
        if preview is not None:
            preview.status = DocumentStatus.PREVIEW_FAILED.value
            preview.error_message = error_message[:1024]
        self._set_document_status(
            document,
            DocumentStatus.PREVIEW_FAILED,
            "preview_failed",
            actor_id,
        )
        self.session.commit()
        self._publish(
            "DocumentPreviewFailed",
            context,
            document,
            preview_id=preview_id,
            parsing_job_id=parsing_job_id,
            error_message=error_message[:1024],
        )

    def _get_document(self, document_id: str) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document")
        return document

    def _set_document_status(
        self,
        document: Document,
        new_status: DocumentStatus,
        reason: str,
        actor_id: str,
    ) -> None:
        previous = document.status
        document.status = new_status.value
        self.status_history.add(
            DocumentStatusHistory(
                document_id=document.id,
                previous_status=previous,
                new_status=new_status.value,
                reason=reason,
                changed_by=actor_id,
            )
        )

    def _publish(
        self,
        event_type: str,
        context: RequestContext,
        document: Document,
        **payload: object,
    ) -> None:
        self.publisher.publish(
            DomainEvent.create(
                event_type,
                context.correlation_id,
                {
                    "document_id": document.id,
                    "client_id": document.client_id,
                    "competence_id": document.competence_id,
                    "file_format": document.file_format,
                    **payload,
                },
            )
        )

from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile, ZipFile

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.context import RequestContext
from app.application.schemas import DocumentResponse, UploadZipResponse, ZipError
from app.config import Settings
from app.domain.enums import (
    DocumentStatus,
    MIME_TYPES,
    UploadBatchStatus,
)
from app.domain.files import (
    extension_for,
    format_for_extension,
    make_stored_filename,
    sanitize_filename,
    storage_key,
    validate_archive_member_path,
)
from app.domain.hashing import sha256_hex
from app.errors import BusinessRuleError, NotFoundError, StorageUnavailableError
from app.infrastructure.database.models import (
    Document,
    DocumentStatusHistory,
    DocumentUploadBatch,
    new_id,
)
from app.infrastructure.events import DomainEvent, EventPublisher
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.repositories import (
    DocumentRepository,
    StatusHistoryRepository,
    UploadBatchRepository,
)
from app.infrastructure.storage import StorageClient


@dataclass(frozen=True)
class UploadCandidate:
    filename: str
    content: bytes
    content_type: str | None = None


class DocumentService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        storage: StorageClient,
        publisher: EventPublisher,
    ) -> None:
        self.session = session
        self.settings = settings
        self.storage = storage
        self.publisher = publisher
        self.documents = DocumentRepository(session)
        self.status_history = StatusHistoryRepository(session)

    def get(self, document_id: str) -> Document:
        document = self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Document")
        return document

    def list(
        self,
        *,
        client_id: str | None,
        competence_id: str | None,
        status: DocumentStatus | None,
        file_format: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Document], int]:
        normalized_format = file_format.upper() if file_format else None
        return self.documents.list(
            client_id=client_id,
            competence_id=competence_id,
            status=status.value if status else None,
            file_format=normalized_format,
            page=page,
            limit=limit,
        )

    def change_status(
        self,
        document_id: str,
        new_status: DocumentStatus,
        reason: str | None,
        actor: Principal,
    ) -> Document:
        document = self.get(document_id)
        previous = document.status
        document.status = new_status.value
        self.status_history.add(
            DocumentStatusHistory(
                document_id=document.id,
                previous_status=previous,
                new_status=new_status.value,
                reason=reason,
                changed_by=actor.id,
            )
        )
        self.session.commit()
        return document


class UploadService(DocumentService):
    def upload_single(
        self,
        *,
        client_id: str,
        competence_id: str,
        candidate: UploadCandidate,
        actor: Principal,
        context: RequestContext,
        allow_zip: bool = False,
    ) -> DocumentResponse:
        self._validate_size(candidate.content, self.settings.max_file_size_bytes)
        metadata = self._inspect_candidate(candidate, allow_zip=allow_zip)
        content_hash = sha256_hex(candidate.content)
        duplicate = self.documents.get_duplicate(client_id, competence_id, content_hash)
        if duplicate is not None:
            response = DocumentResponse.duplicate(duplicate)
            self._publish(
                "DocumentDuplicateDetected",
                context,
                response,
            )
            return response

        document_id = new_id()
        stored_filename = make_stored_filename(metadata["filename"], document_id)
        bucket = self.settings.minio_bucket_documents_original
        key = storage_key(client_id, competence_id, document_id, stored_filename)
        document = Document(
            id=document_id,
            client_id=client_id,
            competence_id=competence_id,
            original_filename=metadata["filename"],
            stored_filename=stored_filename,
            file_extension=metadata["extension"],
            file_format=metadata["file_format"],
            mime_type=metadata["mime_type"],
            size_bytes=len(candidate.content),
            content_hash=content_hash,
            storage_bucket=bucket,
            storage_key=key,
            status=DocumentStatus.UPLOADED.value,
            created_by=actor.id,
        )
        try:
            self.storage.upload_bytes(
                bucket=bucket,
                key=key,
                content=candidate.content,
                content_type=metadata["mime_type"],
                metadata={
                    "client_id": client_id,
                    "competence_id": competence_id,
                    "document_id": document_id,
                    "content_hash": content_hash,
                },
            )
            self.documents.add(document)
            self.status_history.add(
                DocumentStatusHistory(
                    document_id=document.id,
                    previous_status=None,
                    new_status=DocumentStatus.UPLOADED.value,
                    reason="upload_completed",
                    changed_by=actor.id,
                )
            )
            self.session.commit()
        except StorageUnavailableError:
            self._record_storage_failed(document, actor, context)
            raise
        except IntegrityError as exc:
            self.session.rollback()
            duplicate = self.documents.get_duplicate(client_id, competence_id, content_hash)
            if duplicate is not None:
                return DocumentResponse.duplicate(duplicate)
            raise BusinessRuleError(
                "DOCUMENT_ALREADY_EXISTS",
                "Document already exists for this client and competence",
                status_code=409,
            ) from exc
        response = DocumentResponse.from_entity(document)
        self._publish("DocumentUploaded", context, response)
        return response

    def upload_zip(
        self,
        *,
        client_id: str,
        competence_id: str,
        candidate: UploadCandidate,
        actor: Principal,
        context: RequestContext,
    ) -> UploadZipResponse:
        self._validate_size(candidate.content, self.settings.max_zip_size_bytes)
        metadata = self._inspect_candidate(candidate, allow_zip=True)
        if metadata["extension"] != ".zip":
            raise BusinessRuleError("ZIP_REQUIRED", "Upload file must be a ZIP archive")
        documents: list[DocumentResponse] = []
        errors: list[ZipError] = []
        total_files = 0
        try:
            archive = ZipFile(BytesIO(candidate.content))
        except BadZipFile as exc:
            raise BusinessRuleError("INVALID_ZIP", "Invalid ZIP file") from exc
        with archive:
            entries = archive.infolist()
            if len(entries) > self.settings.document_max_files_per_zip:
                raise BusinessRuleError("ZIP_TOO_MANY_FILES", "ZIP contains too many entries")
            for entry in entries:
                if entry.is_dir():
                    errors.append(ZipError(filename=entry.filename, reason="directory_not_supported"))
                    continue
                total_files += 1
                try:
                    filename = validate_archive_member_path(entry.filename)
                    extension = extension_for(filename)
                    if extension == ".zip":
                        raise BusinessRuleError("NESTED_ZIP_NOT_SUPPORTED", "Nested ZIP is not supported")
                    if extension not in self.settings.allowed_extensions:
                        raise BusinessRuleError("UNSUPPORTED_FILE_TYPE", "Unsupported file type")
                    content = archive.read(entry)
                    self._validate_size(content, self.settings.max_file_size_bytes)
                    documents.append(
                        self.upload_single(
                            client_id=client_id,
                            competence_id=competence_id,
                            candidate=UploadCandidate(
                                filename=filename,
                                content=content,
                                content_type=MIME_TYPES.get(extension),
                            ),
                            actor=actor,
                            context=context,
                            allow_zip=False,
                        )
                    )
                except BusinessRuleError as exc:
                    errors.append(ZipError(filename=entry.filename, reason=exc.code.lower()))
                    self._publish_rejected(entry.filename, client_id, competence_id, context, exc.code)

        created_count = sum(1 for item in documents if not item.is_duplicate)
        duplicate_count = sum(1 for item in documents if item.is_duplicate)
        rejected_count = len(errors)
        batch_status = (
            UploadBatchStatus.COMPLETED
            if rejected_count == 0
            else UploadBatchStatus.COMPLETED_WITH_ERRORS
        )
        batch = DocumentUploadBatch(
            client_id=client_id,
            competence_id=competence_id,
            original_filename=metadata["filename"],
            total_files=total_files,
            created_count=created_count,
            duplicate_count=duplicate_count,
            rejected_count=rejected_count,
            status=batch_status.value,
            created_by=actor.id,
        )
        UploadBatchRepository(self.session).add(batch)
        self.session.commit()
        return UploadZipResponse.from_batch(batch, documents, errors)

    def _inspect_candidate(self, candidate: UploadCandidate, *, allow_zip: bool) -> dict[str, str | None]:
        filename = sanitize_filename(candidate.filename)
        extension = extension_for(filename)
        if extension not in self.settings.allowed_extensions:
            raise BusinessRuleError("UNSUPPORTED_FILE_TYPE", "Unsupported file type")
        if extension == ".zip" and not allow_zip:
            raise BusinessRuleError("ZIP_UPLOAD_ENDPOINT_REQUIRED", "Use /documents/upload-zip for ZIP files")
        file_format = format_for_extension(extension)
        return {
            "filename": filename,
            "extension": extension,
            "file_format": file_format.value,
            "mime_type": candidate.content_type or MIME_TYPES.get(extension),
        }

    def _validate_size(self, content: bytes, limit: int) -> None:
        if not content:
            raise BusinessRuleError("EMPTY_FILE", "File is empty")
        if len(content) > limit:
            raise BusinessRuleError("FILE_TOO_LARGE", "File exceeds configured size limit")

    def _record_storage_failed(
        self,
        document: Document,
        actor: Principal,
        context: RequestContext,
    ) -> None:
        self.session.rollback()
        document.status = DocumentStatus.STORAGE_FAILED.value
        self.session.add(document)
        self.session.flush()
        self.status_history.add(
            DocumentStatusHistory(
                document_id=document.id,
                previous_status=None,
                new_status=DocumentStatus.STORAGE_FAILED.value,
                reason="storage_failed",
                changed_by=actor.id,
            )
        )
        self.session.commit()
        response = DocumentResponse.from_entity(document)
        self._publish("DocumentStorageFailed", context, response)

    def _publish(
        self,
        event_type: str,
        context: RequestContext,
        response: DocumentResponse,
    ) -> None:
        self.publisher.publish(
            DomainEvent.create(
                event_type,
                context.correlation_id,
                {
                    "document_id": response.document_id,
                    "client_id": response.client_id,
                    "competence_id": response.competence_id,
                    "original_filename": response.original_filename,
                    "file_format": response.file_format.value,
                    "content_hash": response.content_hash,
                    "status": response.status.value,
                },
            )
        )

    def _publish_rejected(
        self,
        filename: str,
        client_id: str,
        competence_id: str,
        context: RequestContext,
        reason: str,
    ) -> None:
        self.publisher.publish(
            DomainEvent.create(
                "DocumentRejected",
                context.correlation_id,
                {
                    "client_id": client_id,
                    "competence_id": competence_id,
                    "original_filename": filename,
                    "reason": reason,
                    "status": DocumentStatus.REJECTED.value,
                },
            )
        )

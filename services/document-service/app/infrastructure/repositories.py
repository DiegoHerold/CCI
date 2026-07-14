from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import (
    Document,
    DocumentParsingJob,
    DocumentPreview,
    DocumentStatusHistory,
    DocumentUploadBatch,
)


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, document_id: str) -> Document | None:
        return self.session.get(Document, document_id)

    def get_duplicate(
        self, client_id: str, competence_id: str, content_hash: str
    ) -> Document | None:
        return self.session.scalar(
            select(Document).where(
                Document.client_id == client_id,
                Document.competence_id == competence_id,
                Document.content_hash == content_hash,
            )
        )

    def add(self, document: Document) -> Document:
        self.session.add(document)
        self.session.flush()
        return document

    def list(
        self,
        *,
        client_id: str | None,
        competence_id: str | None,
        status: str | None,
        file_format: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[Document], int]:
        statement = select(Document)
        if client_id:
            statement = statement.where(Document.client_id == client_id)
        if competence_id:
            statement = statement.where(Document.competence_id == competence_id)
        if status:
            statement = statement.where(Document.status == status)
        if file_format:
            statement = statement.where(Document.file_format == file_format)
        total = self.session.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        ) or 0
        statement = (
            statement.order_by(Document.created_at.desc(), Document.id.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all()), int(total)


class UploadBatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, batch: DocumentUploadBatch) -> DocumentUploadBatch:
        self.session.add(batch)
        self.session.flush()
        return batch


class PreviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, preview: DocumentPreview) -> DocumentPreview:
        self.session.add(preview)
        self.session.flush()
        return preview

    def get(self, preview_id: str) -> DocumentPreview | None:
        return self.session.get(DocumentPreview, preview_id)

    def latest_for_document(self, document_id: str) -> DocumentPreview | None:
        return self.session.scalar(
            select(DocumentPreview)
            .where(DocumentPreview.document_id == document_id)
            .order_by(DocumentPreview.created_at.desc(), DocumentPreview.id.desc())
            .limit(1)
        )


class ParsingJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, job: DocumentParsingJob) -> DocumentParsingJob:
        self.session.add(job)
        self.session.flush()
        return job

    def get(self, job_id: str) -> DocumentParsingJob | None:
        return self.session.get(DocumentParsingJob, job_id)

    def latest_for_document(self, document_id: str) -> DocumentParsingJob | None:
        return self.session.scalar(
            select(DocumentParsingJob)
            .where(DocumentParsingJob.document_id == document_id)
            .order_by(DocumentParsingJob.created_at.desc(), DocumentParsingJob.id.desc())
            .limit(1)
        )


class StatusHistoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, history: DocumentStatusHistory) -> DocumentStatusHistory:
        self.session.add(history)
        self.session.flush()
        return history

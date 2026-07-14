from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import (
    ALLOWED_TRANSITIONS,
    ExtractionAttemptStatus,
    ExtractionArtifactType,
    ExtractionJobStatus,
)
from app.errors import BusinessRuleError, NotFoundError
from app.infrastructure.database.models import (
    ExtractionArtifact,
    ExtractionAttempt,
    ExtractionJob,
    ExtractionJobStatusHistory,
)


class ExtractionJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_job(
        self,
        *,
        document_id: str,
        client_id: str,
        competence_id: str,
        template_id: str,
        template_version_id: str,
        matching_run_id: str | None,
        file_format: str,
        requested_by: str,
        max_attempts: int,
    ) -> ExtractionJob:
        job = ExtractionJob(
            document_id=document_id,
            client_id=client_id,
            competence_id=competence_id,
            template_id=template_id,
            template_version_id=template_version_id,
            matching_run_id=matching_run_id,
            file_format=file_format,
            status=ExtractionJobStatus.PENDING.value,
            requested_by=requested_by,
            max_attempts=max_attempts,
        )
        self.session.add(job)
        self.session.flush()
        self.record_status(job, None, ExtractionJobStatus.PENDING, "job_created", requested_by)
        return job

    def get(self, job_id: str) -> ExtractionJob:
        job = self.session.execute(
            select(ExtractionJob)
            .where(ExtractionJob.id == job_id)
            .options(
                selectinload(ExtractionJob.history),
                selectinload(ExtractionJob.attempts),
                selectinload(ExtractionJob.artifacts),
            )
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()
        if job is None:
            raise NotFoundError("extraction job")
        return job

    def list_by_document(self, document_id: str) -> list[ExtractionJob]:
        return list(
            self.session.execute(
                select(ExtractionJob)
                .where(ExtractionJob.document_id == document_id)
                .order_by(desc(ExtractionJob.created_at))
            ).scalars()
        )

    def latest_by_document(self, document_id: str) -> ExtractionJob | None:
        return self.session.execute(
            select(ExtractionJob)
            .where(ExtractionJob.document_id == document_id)
            .order_by(desc(ExtractionJob.created_at))
            .limit(1)
        ).scalar_one_or_none()

    def latest_completed_by_document(self, document_id: str) -> ExtractionJob | None:
        return self.session.execute(
            select(ExtractionJob)
            .where(
                ExtractionJob.document_id == document_id,
                ExtractionJob.status == ExtractionJobStatus.COMPLETED.value,
            )
            .order_by(desc(ExtractionJob.created_at))
            .limit(1)
        ).scalar_one_or_none()

    def transition(
        self,
        job: ExtractionJob,
        new_status: ExtractionJobStatus,
        *,
        reason: str | None = None,
        changed_by: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ExtractionJob:
        current = ExtractionJobStatus(job.status)
        if new_status not in ALLOWED_TRANSITIONS[current] and current != new_status:
            raise BusinessRuleError(
                "INVALID_EXTRACTION_STATUS_TRANSITION",
                f"Cannot transition extraction job from {current.value} to {new_status.value}",
                status_code=409,
            )
        previous = job.status
        job.status = new_status.value
        job.error_code = error_code
        job.error_message = error_message
        now = datetime.now(UTC)
        if new_status in {ExtractionJobStatus.STARTING, ExtractionJobStatus.RUNNING} and job.started_at is None:
            job.started_at = now
        if new_status in {
            ExtractionJobStatus.COMPLETED,
            ExtractionJobStatus.FAILED,
            ExtractionJobStatus.CANCELLED,
            ExtractionJobStatus.REQUIRES_REVIEW,
        }:
            job.finished_at = now
        self.record_status(job, previous, new_status, reason, changed_by)
        self.session.flush()
        return job

    def record_status(
        self,
        job: ExtractionJob,
        previous_status: str | None,
        new_status: ExtractionJobStatus,
        reason: str | None,
        changed_by: str | None,
    ) -> None:
        self.session.add(
            ExtractionJobStatusHistory(
                extraction_job_id=job.id,
                previous_status=previous_status,
                new_status=new_status.value,
                reason=reason,
                changed_by=changed_by,
            )
        )

    def create_attempt(
        self,
        job: ExtractionJob,
        *,
        status: ExtractionAttemptStatus,
        worker_type: str,
        worker_name: str,
    ) -> ExtractionAttempt:
        job.attempt_count += 1
        attempt = ExtractionAttempt(
            extraction_job_id=job.id,
            attempt_number=job.attempt_count,
            status=status.value,
            worker_type=worker_type,
            worker_name=worker_name,
            started_at=datetime.now(UTC),
        )
        self.session.add(attempt)
        self.session.flush()
        return attempt

    def finish_attempt(
        self,
        attempt: ExtractionAttempt,
        *,
        status: ExtractionAttemptStatus,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ExtractionAttempt:
        attempt.status = status.value
        attempt.error_code = error_code
        attempt.error_message = error_message
        attempt.finished_at = datetime.now(UTC)
        self.session.flush()
        return attempt

    def add_artifact(
        self,
        job: ExtractionJob,
        *,
        artifact_type: ExtractionArtifactType,
        storage_bucket: str,
        storage_key: str,
        content_hash: str | None,
    ) -> ExtractionArtifact:
        artifact = ExtractionArtifact(
            extraction_job_id=job.id,
            document_id=job.document_id,
            artifact_type=artifact_type.value,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            content_hash=content_hash,
        )
        self.session.add(artifact)
        self.session.flush()
        return artifact

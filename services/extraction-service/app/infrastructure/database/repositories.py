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
    ExtractedArrayItem,
    ExtractedFieldReview,
    ExtractedFieldValue,
    ExtractedObject,
    ExtractionEvidence,
    ExtractionArtifact,
    ExtractionAttempt,
    ExtractionJob,
    ExtractionJobStatusHistory,
    ExtractionResult,
    NormalizationRun,
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


class ExtractionResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_result(
        self,
        *,
        job: ExtractionJob,
        status: str,
        field_count: int,
        normalized_count: int,
        requires_review_count: int,
        error_count: int,
        warning_count: int,
    ) -> ExtractionResult:
        result = ExtractionResult(
            extraction_job_id=job.id,
            document_id=job.document_id,
            client_id=job.client_id,
            competence_id=job.competence_id,
            template_id=job.template_id,
            template_version_id=job.template_version_id,
            status=status,
            field_count=field_count,
            normalized_count=normalized_count,
            requires_review_count=requires_review_count,
            error_count=error_count,
            warning_count=warning_count,
        )
        self.session.add(result)
        self.session.flush()
        return result

    def add_object(
        self,
        *,
        result: ExtractionResult,
        field_path: str,
        field_type: str,
        object_type: str | None = None,
        item_index: int | None = None,
        status: str = "normalized",
        parent_object_id: str | None = None,
    ) -> ExtractedObject:
        item = ExtractedObject(
            extraction_result_id=result.id,
            parent_object_id=parent_object_id,
            field_path=field_path,
            field_type=field_type,
            object_type=object_type,
            item_index=item_index,
            status=status,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def add_array_item(
        self,
        *,
        result: ExtractionResult,
        array_field_path: str,
        item_index: int,
        status: str,
        confidence: float,
    ) -> ExtractedArrayItem:
        item = ExtractedArrayItem(
            extraction_result_id=result.id,
            array_field_path=array_field_path,
            item_index=item_index,
            status=status,
            confidence=confidence,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def add_field_value(
        self,
        *,
        result: ExtractionResult,
        field_id: str | None,
        field_path: str,
        field_type: str,
        raw_value: object | None,
        normalized_value: str | None,
        display_value: str | None,
        normalized_json: object | None,
        metadata_json: object | None,
        confidence: float,
        status: str,
        is_required: bool,
        item_index: int | None = None,
        extracted_object_id: str | None = None,
    ) -> ExtractedFieldValue:
        item = ExtractedFieldValue(
            extraction_result_id=result.id,
            extracted_object_id=extracted_object_id,
            field_id=field_id,
            field_path=field_path,
            field_type=field_type,
            raw_value=raw_value,
            normalized_value=normalized_value,
            display_value=display_value,
            normalized_json=normalized_json,
            metadata_json=metadata_json,
            confidence=confidence,
            status=status,
            is_required=is_required,
            item_index=item_index,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def add_evidence(
        self,
        *,
        result: ExtractionResult,
        field_value_id: str | None,
        document_id: str,
        evidence: dict,
        template_id: str,
        template_version_id: str,
    ) -> ExtractionEvidence:
        item = ExtractionEvidence(
            extraction_result_id=result.id,
            document_id=document_id,
            field_value_id=field_value_id,
            evidence_type=str(evidence.get("evidence_type") or "unknown"),
            page_number=evidence.get("page_number"),
            bbox_json=evidence.get("bbox"),
            sheet_name=evidence.get("sheet_name"),
            cell_range=evidence.get("cell_range"),
            source_text=evidence.get("source_text"),
            source_value=evidence.get("source_value"),
            rule_id=evidence.get("rule_id"),
            rule_strategy=evidence.get("rule_strategy"),
            template_id=template_id,
            template_version_id=template_version_id,
            confidence=evidence.get("confidence"),
        )
        self.session.add(item)
        self.session.flush()
        if field_value_id is not None:
            field = self.session.get(ExtractedFieldValue, field_value_id)
            if field is not None:
                field.evidence_id = item.id
        return item

    def create_run(self, *, job: ExtractionJob, status: str) -> NormalizationRun:
        run = NormalizationRun(extraction_job_id=job.id, status=status)
        self.session.add(run)
        self.session.flush()
        return run

    def get_result(self, result_id: str) -> ExtractionResult:
        result = self.session.execute(
            select(ExtractionResult).where(ExtractionResult.id == result_id).execution_options(populate_existing=True)
        ).scalar_one_or_none()
        if result is None:
            raise NotFoundError("extraction result")
        return result

    def get_by_job(self, job_id: str) -> ExtractionResult:
        result = self.session.execute(
            select(ExtractionResult)
            .where(ExtractionResult.extraction_job_id == job_id)
            .order_by(desc(ExtractionResult.created_at))
            .limit(1)
        ).scalar_one_or_none()
        if result is None:
            raise NotFoundError("extraction result")
        return result

    def latest_by_document(self, document_id: str) -> ExtractionResult:
        result = self.session.execute(
            select(ExtractionResult)
            .where(ExtractionResult.document_id == document_id)
            .order_by(desc(ExtractionResult.created_at))
            .limit(1)
        ).scalar_one_or_none()
        if result is None:
            raise NotFoundError("extraction result")
        return result

    def list_fields(
        self,
        result_id: str,
        *,
        field_path: str | None = None,
        status: str | None = None,
        field_type: str | None = None,
        requires_review: bool | None = None,
        min_confidence: float | None = None,
    ) -> list[ExtractedFieldValue]:
        query = select(ExtractedFieldValue).where(ExtractedFieldValue.extraction_result_id == result_id)
        if field_path:
            query = query.where(ExtractedFieldValue.field_path == field_path)
        if status:
            query = query.where(ExtractedFieldValue.status == status)
        if field_type:
            query = query.where(ExtractedFieldValue.field_type == field_type)
        if requires_review is not None:
            review_statuses = {"requires_review", "normalization_failed", "low_confidence", "evidence_missing", "ambiguous"}
            query = query.where(ExtractedFieldValue.status.in_(review_statuses) if requires_review else ~ExtractedFieldValue.status.in_(review_statuses))
        if min_confidence is not None:
            query = query.where(ExtractedFieldValue.confidence >= min_confidence)
        return list(self.session.execute(query.order_by(ExtractedFieldValue.field_path, ExtractedFieldValue.item_index)).scalars())

    def get_field(self, result_id: str, field_value_id: str) -> ExtractedFieldValue:
        field = self.session.execute(
            select(ExtractedFieldValue).where(
                ExtractedFieldValue.id == field_value_id,
                ExtractedFieldValue.extraction_result_id == result_id,
            )
        ).scalar_one_or_none()
        if field is None:
            raise NotFoundError("extracted field")
        return field

    def get_field_any_result(self, field_value_id: str) -> ExtractedFieldValue:
        field = self.session.get(ExtractedFieldValue, field_value_id)
        if field is None:
            raise NotFoundError("extracted field")
        return field

    def list_objects(self, result_id: str) -> list[ExtractedObject]:
        return list(
            self.session.execute(
                select(ExtractedObject)
                .where(ExtractedObject.extraction_result_id == result_id)
                .order_by(ExtractedObject.field_path, ExtractedObject.item_index)
            ).scalars()
        )

    def list_array_items(self, result_id: str, field_path: str) -> list[ExtractedArrayItem]:
        return list(
            self.session.execute(
                select(ExtractedArrayItem)
                .where(
                    ExtractedArrayItem.extraction_result_id == result_id,
                    ExtractedArrayItem.array_field_path == field_path,
                )
                .order_by(ExtractedArrayItem.item_index)
            ).scalars()
        )

    def list_evidence_for_field(self, field_value_id: str) -> list[ExtractionEvidence]:
        return list(
            self.session.execute(
                select(ExtractionEvidence)
                .where(ExtractionEvidence.field_value_id == field_value_id)
                .order_by(ExtractionEvidence.created_at)
            ).scalars()
        )

    def record_field_review(
        self,
        field: ExtractedFieldValue,
        *,
        action: str,
        reviewed_by: str,
        reason: str | None = None,
        new_raw_value: object | None = None,
        new_normalized_value: str | None = None,
        new_display_value: str | None = None,
        new_normalized_json: object | None = None,
        new_metadata_json: object | None = None,
        new_status: str,
    ) -> ExtractedFieldReview:
        review = ExtractedFieldReview(
            extraction_result_id=field.extraction_result_id,
            field_value_id=field.id,
            action=action,
            previous_status=field.status,
            previous_raw_value=field.raw_value,
            previous_normalized_value=field.normalized_value,
            previous_display_value=field.display_value,
            previous_normalized_json=field.normalized_json,
            new_raw_value=new_raw_value if new_raw_value is not None else field.raw_value,
            new_normalized_value=new_normalized_value,
            new_display_value=new_display_value,
            new_normalized_json=new_normalized_json,
            reason=reason,
            reviewed_by=reviewed_by,
        )
        self.session.add(review)
        if action == "correct":
            field.raw_value = new_raw_value
            field.normalized_value = new_normalized_value
            field.display_value = new_display_value
            field.normalized_json = new_normalized_json
            field.metadata_json = new_metadata_json
            field.confidence = 1.0
        field.status = new_status
        self._refresh_result_counts(field.extraction_result_id)
        self.session.flush()
        return review

    def _refresh_result_counts(self, result_id: str) -> None:
        result = self.get_result(result_id)
        fields = list(
            self.session.execute(
                select(ExtractedFieldValue).where(ExtractedFieldValue.extraction_result_id == result_id)
            ).scalars()
        )
        review_statuses = {"requires_review", "normalization_failed", "low_confidence", "evidence_missing", "ambiguous", "not_found"}
        result.field_count = len(fields)
        result.normalized_count = sum(1 for field in fields if field.status in {"normalized", "approved", "corrected"})
        result.requires_review_count = sum(1 for field in fields if field.status in review_statuses)
        if result.requires_review_count:
            result.status = "requires_review"
        elif result.error_count or result.warning_count:
            result.status = "completed_with_warnings"
        else:
            result.status = "completed"

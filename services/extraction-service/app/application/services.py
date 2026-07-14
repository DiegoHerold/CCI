from typing import Any

from sqlalchemy.orm import Session

from app.application.schemas import ExtractionReprocessRequest, ExtractionRequest
from app.config import Settings
from app.domain.enums import (
    ExtractionArtifactType,
    ExtractionAttemptStatus,
    ExtractionJobStatus,
    ExtractionResultStatus,
    TERMINAL_STATUSES,
)
from app.errors import BusinessRuleError, ConflictError, NotFoundError, ServiceError
from app.infrastructure.clients.document_service import DocumentServiceHttpAdapter
from app.infrastructure.clients.template_service import TemplateServiceHttpAdapter
from app.infrastructure.database.models import ExtractionJob
from app.infrastructure.database.repositories import ExtractionJobRepository
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.messaging.events import DomainEvent, EventPublisher
from app.infrastructure.storage.artifact_storage import ArtifactStorage
from app.infrastructure.temporal.client import TemporalClient
from app.infrastructure.worker_dispatch import WorkerDispatcher
from app.modules.results.service import ExtractionResultService


class ExtractionService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        document_service: DocumentServiceHttpAdapter,
        template_service: TemplateServiceHttpAdapter,
        temporal_client: TemporalClient,
        dispatcher: WorkerDispatcher,
        storage: ArtifactStorage,
        publisher: EventPublisher,
    ) -> None:
        self.session = session
        self.settings = settings
        self.document_service = document_service
        self.template_service = template_service
        self.temporal_client = temporal_client
        self.dispatcher = dispatcher
        self.storage = storage
        self.publisher = publisher
        self.jobs = ExtractionJobRepository(session)
        self.results = ExtractionResultService(session, settings)

    async def request_extraction_for_document(
        self,
        document_id: str,
        payload: ExtractionRequest,
        actor: Principal,
        correlation_id: str,
    ) -> ExtractionJob:
        actor.require_permission("documents:read")
        if not payload.force_reprocess:
            completed = self.jobs.latest_completed_by_document(document_id)
            if completed is not None:
                return completed

        document = await self.document_service.get_document(
            document_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        preview = await self.document_service.get_preview(
            document_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        self._validate_preview(preview)

        matching = await self._resolve_matching(document_id, payload, actor, correlation_id)
        template_id = payload.template_id or matching["matchedTemplateId"]
        template_version_id = payload.template_version_id or matching["matchedTemplateVersionId"]
        if not template_id or not template_version_id:
            raise BusinessRuleError("TEMPLATE_NOT_CONFIRMED", "Document does not have a confirmed template")

        template = await self.template_service.get_template(
            template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        version = await self.template_service.get_template_version(
            template_id,
            template_version_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        fields = await self.template_service.get_fields(
            template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        rules = await self.template_service.get_extraction_rules(
            template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        self._validate_template_inputs(document, template, version, fields, rules)

        job = self.jobs.create_job(
            document_id=document["documentId"],
            client_id=document["clientId"],
            competence_id=document["competenceId"],
            template_id=template_id,
            template_version_id=template_version_id,
            matching_run_id=matching.get("matchingRunId"),
            file_format=self._normalized_file_format(document),
            requested_by=actor.id,
            max_attempts=self.settings.extraction_max_attempts,
        )
        workflow_payload = {
            "extraction_job_id": job.id,
            "document_id": job.document_id,
            "client_id": job.client_id,
            "competence_id": job.competence_id,
            "template_id": job.template_id,
            "template_version_id": job.template_version_id,
            "file_format": job.file_format,
        }
        workflow = await self.temporal_client.start_extraction_workflow(workflow_payload)
        job.workflow_id = workflow.workflow_id
        job.workflow_run_id = workflow.workflow_run_id
        self.jobs.transition(job, ExtractionJobStatus.QUEUED, reason="workflow_started", changed_by=actor.id)
        self.session.commit()

        await self._safe_document_status(
            job.document_id,
            "extraction_pending",
            actor,
            correlation_id,
            "Extraction job queued",
        )
        self._publish("ExtractionRequested", job, correlation_id)
        return self.jobs.get(job.id)

    def get_job(self, job_id: str) -> ExtractionJob:
        return self.jobs.get(job_id)

    def list_jobs_for_document(self, document_id: str) -> list[ExtractionJob]:
        return self.jobs.list_by_document(document_id)

    def latest_for_document(self, document_id: str) -> ExtractionJob:
        job = self.jobs.latest_by_document(document_id)
        if job is None:
            raise NotFoundError("extraction job")
        return job

    async def retry_job(self, job_id: str, actor: Principal, correlation_id: str) -> ExtractionJob:
        actor.require_permission("documents:read")
        job = self.jobs.get(job_id)
        if job.status != ExtractionJobStatus.FAILED.value:
            raise ConflictError("EXTRACTION_RETRY_NOT_ALLOWED", "Only failed extraction jobs can be retried")
        if job.attempt_count >= job.max_attempts:
            raise ConflictError("EXTRACTION_RETRY_LIMIT_EXCEEDED", "Extraction retry limit exceeded")
        job.finished_at = None
        self.jobs.transition(job, ExtractionJobStatus.RETRYING, reason="manual_retry_requested", changed_by=actor.id)
        self.jobs.transition(job, ExtractionJobStatus.QUEUED, reason="retry_queued", changed_by=actor.id)
        self.session.commit()
        self._publish("ExtractionRetryScheduled", job, correlation_id)
        return self.jobs.get(job_id)

    async def cancel_job(self, job_id: str, actor: Principal, correlation_id: str) -> ExtractionJob:
        actor.require_permission("documents:read")
        job = self.jobs.get(job_id)
        if ExtractionJobStatus(job.status) in TERMINAL_STATUSES:
            raise ConflictError("EXTRACTION_CANCEL_NOT_ALLOWED", "Terminal extraction jobs cannot be cancelled")
        if job.workflow_id:
            await self.temporal_client.cancel_workflow(job.workflow_id)
        self.jobs.transition(job, ExtractionJobStatus.CANCELLED, reason="manual_cancel", changed_by=actor.id)
        self.session.commit()
        await self._safe_document_status(job.document_id, "extraction_failed", actor, correlation_id, "Extraction cancelled")
        self._publish("ExtractionCancelled", job, correlation_id)
        return self.jobs.get(job_id)

    async def reprocess_document(
        self,
        document_id: str,
        payload: ExtractionReprocessRequest,
        actor: Principal,
        correlation_id: str,
    ) -> ExtractionJob:
        request = ExtractionRequest(
            force_reprocess=True,
            template_version_id=payload.template_version_id,
        )
        return await self.request_extraction_for_document(document_id, request, actor, correlation_id)

    async def run_job_once(self, job_id: str, actor: Principal, correlation_id: str) -> ExtractionJob:
        """Called by the prepared workflow/worker bootstrap or by tests with a fake dispatcher."""
        job = self.jobs.get(job_id)
        if job.status not in {ExtractionJobStatus.QUEUED.value, ExtractionJobStatus.RETRYING.value}:
            raise ConflictError("EXTRACTION_JOB_NOT_QUEUED", "Extraction job is not queued")
        try:
            self.jobs.transition(job, ExtractionJobStatus.STARTING, reason="workflow_activity_started", changed_by="workflow")
            self.jobs.transition(job, ExtractionJobStatus.RUNNING, reason="inputs_loading", changed_by="workflow")
            self._publish("ExtractionStarted", job, correlation_id)
            await self._safe_document_status(job.document_id, "extraction_running", actor, correlation_id, "Extraction running")
            self.jobs.transition(job, ExtractionJobStatus.WAITING_WORKER, reason="worker_selection", changed_by="workflow")
            selection = self.dispatcher.choose_worker(job.file_format)
            attempt = self.jobs.create_attempt(
                job,
                status=ExtractionAttemptStatus.WORKER_RUNNING,
                worker_type=selection.worker_type.value,
                worker_name=selection.worker_name,
            )
            self.jobs.transition(job, ExtractionJobStatus.WORKER_RUNNING, reason="worker_dispatched", changed_by="workflow")
            self.session.flush()
            self._publish(
                "ExtractionWorkerDispatched",
                job,
                correlation_id,
                extra={"worker_name": selection.worker_name, "task_queue": selection.task_queue},
            )
            worker_payload = await self._build_worker_payload(job, actor, correlation_id)
            result = await self.dispatcher.dispatch(worker_payload, selection)
            if result.status not in {"completed", "completed_with_warnings"}:
                errors = result.errors or ["Worker did not complete extraction"]
                raise BusinessRuleError("EXTRACTION_WORKER_FAILED", "; ".join(errors))
            key = self.storage.generate_key(
                client_id=job.client_id,
                competence_id=job.competence_id,
                document_id=job.document_id,
                job_id=job.id,
            )
            bucket, content_hash = self.storage.save_json(key, result.raw_output)
            artifact = self.jobs.add_artifact(
                job,
                artifact_type=ExtractionArtifactType.WORKER_RAW_OUTPUT,
                storage_bucket=bucket,
                storage_key=key,
                content_hash=content_hash,
            )
            self._publish("ExtractionNormalizationStarted", job, correlation_id)
            try:
                normalization = self.results.process_worker_output(
                    job=job,
                    raw_output=result.raw_output,
                    fields=worker_payload.get("template", {}).get("fields", []),
                )
            except ValueError as exc:
                self._publish_normalization_failed(job, correlation_id, str(exc))
                raise BusinessRuleError("EXTRACTION_NORMALIZATION_FAILED", str(exc)) from exc
            self._publish(
                "ExtractionResultsSaved",
                job,
                correlation_id,
                extra={
                    "extraction_result_id": normalization.result.id,
                    "status": normalization.result.status,
                    "field_count": normalization.result.field_count,
                    "requires_review_count": normalization.result.requires_review_count,
                },
            )
            self._publish(
                "ExtractionNormalizationCompleted",
                job,
                correlation_id,
                extra={"extraction_result_id": normalization.result.id, "status": normalization.result.status},
            )
            self.jobs.finish_attempt(attempt, status=ExtractionAttemptStatus.COMPLETED)
            final_status = (
                ExtractionJobStatus.REQUIRES_REVIEW
                if normalization.status == ExtractionResultStatus.REQUIRES_REVIEW
                else ExtractionJobStatus.COMPLETED
            )
            self.jobs.transition(job, final_status, reason="normalization_completed", changed_by="workflow")
            self.session.commit()
            if final_status == ExtractionJobStatus.REQUIRES_REVIEW:
                await self._safe_document_status(job.document_id, "review_pending", actor, correlation_id, "Extraction requires review")
                self._publish(
                    "ExtractionRequiresReview",
                    job,
                    correlation_id,
                    extra={
                        "extraction_result_id": normalization.result.id,
                        "reason": "low_confidence_or_missing_required_fields",
                    },
                )
            else:
                await self._safe_document_status(job.document_id, "extracted", actor, correlation_id, "Extraction completed")
            self._publish(
                "ExtractionCompleted",
                job,
                correlation_id,
                extra={"artifact_id": artifact.id, "extraction_result_id": normalization.result.id},
            )
        except ServiceError as exc:
            self._mark_failed(job, actor.id, correlation_id, exc.code, exc.message)
            await self._safe_document_status(job.document_id, "extraction_failed", actor, correlation_id, exc.message)
        return self.jobs.get(job_id)

    def get_result_for_job(self, job_id: str):
        return self.results.repository.get_by_job(job_id)

    def latest_result_for_document(self, document_id: str):
        return self.results.repository.latest_by_document(document_id)

    def list_result_fields(
        self,
        result_id: str,
        *,
        field_path: str | None = None,
        status: str | None = None,
        field_type: str | None = None,
        requires_review: bool | None = None,
        min_confidence: float | None = None,
    ):
        self.results.repository.get_result(result_id)
        return self.results.repository.list_fields(
            result_id,
            field_path=field_path,
            status=status,
            field_type=field_type,
            requires_review=requires_review,
            min_confidence=min_confidence,
        )

    def get_result_field(self, result_id: str, field_value_id: str):
        return self.results.repository.get_field(result_id, field_value_id)

    def list_result_objects(self, result_id: str):
        self.results.repository.get_result(result_id)
        return self.results.repository.list_objects(result_id)

    def list_array_items(self, result_id: str, field_path: str):
        self.results.repository.get_result(result_id)
        return self.results.repository.list_array_items(result_id, field_path)

    def list_field_evidence(self, field_value_id: str):
        self.results.repository.get_field_any_result(field_value_id)
        return self.results.repository.list_evidence_for_field(field_value_id)

    async def reprocess_normalization(self, job_id: str, actor: Principal, correlation_id: str, reason: str | None = None):
        actor.require_permission("documents:read")
        job = self.jobs.get(job_id)
        raw_artifact = next((item for item in reversed(job.artifacts) if item.artifact_type == ExtractionArtifactType.WORKER_RAW_OUTPUT.value), None)
        if raw_artifact is None:
            raise BusinessRuleError("EXTRACTION_RAW_ARTIFACT_NOT_FOUND", "Extraction job has no raw worker artifact")
        raw_output = self.storage.load_json(bucket=raw_artifact.storage_bucket, key=raw_artifact.storage_key)
        fields = await self.template_service.get_fields(
            job.template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        self._publish("ExtractionNormalizationStarted", job, correlation_id, extra={"reason": reason})
        try:
            normalization = self.results.process_worker_output(job=job, raw_output=raw_output, fields=fields)
        except ValueError as exc:
            self._publish_normalization_failed(job, correlation_id, str(exc), extra={"reason": reason})
            raise BusinessRuleError("EXTRACTION_NORMALIZATION_FAILED", str(exc)) from exc
        self.session.commit()
        self._publish(
            "ExtractionResultsSaved",
            job,
            correlation_id,
            extra={
                "extraction_result_id": normalization.result.id,
                "status": normalization.result.status,
                "field_count": normalization.result.field_count,
                "requires_review_count": normalization.result.requires_review_count,
            },
        )
        self._publish(
            "ExtractionNormalizationCompleted",
            job,
            correlation_id,
            extra={"extraction_result_id": normalization.result.id, "status": normalization.result.status},
        )
        return normalization.result

    def _mark_failed(self, job: ExtractionJob, actor_id: str, correlation_id: str, code: str, message: str) -> None:
        for attempt in job.attempts:
            if attempt.status == ExtractionAttemptStatus.WORKER_RUNNING.value:
                self.jobs.finish_attempt(
                    attempt,
                    status=ExtractionAttemptStatus.FAILED,
                    error_code=code,
                    error_message=message,
                )
        self.jobs.transition(
            job,
            ExtractionJobStatus.FAILED,
            reason=code,
            changed_by=actor_id,
            error_code=code,
            error_message=message,
        )
        self.session.commit()
        self._publish("ExtractionFailed", job, correlation_id, extra={"error_code": code, "error_message": message})

    def _publish_normalization_failed(
        self,
        job: ExtractionJob,
        correlation_id: str,
        message: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {"error_code": "EXTRACTION_NORMALIZATION_FAILED", "error_message": message}
        if extra:
            payload.update(extra)
        self._publish("ExtractionNormalizationFailed", job, correlation_id, extra=payload)

    async def _resolve_matching(
        self,
        document_id: str,
        payload: ExtractionRequest,
        actor: Principal,
        correlation_id: str,
    ) -> dict[str, Any]:
        if payload.template_id and payload.template_version_id:
            return {
                "matchingRunId": payload.matching_run_id,
                "status": "manual_override",
                "matchedTemplateId": payload.template_id,
                "matchedTemplateVersionId": payload.template_version_id,
            }
        if payload.matching_run_id:
            matching = await self.template_service.get_matching_run(
                payload.matching_run_id,
                authorization=actor.authorization,
                correlation_id=correlation_id,
            )
        else:
            matching = await self.template_service.get_latest_matching(
                document_id,
                authorization=actor.authorization,
                correlation_id=correlation_id,
            )
        if not matching:
            raise BusinessRuleError("TEMPLATE_NOT_FOUND", "Document has no template matching run")
        status = matching.get("status")
        if status == "not_found":
            raise BusinessRuleError("TEMPLATE_NOT_FOUND", "No template matched this document")
        if status == "ambiguous":
            raise BusinessRuleError("TEMPLATE_AMBIGUOUS", "Template matching is ambiguous")
        if status not in {"matched", "manual_override"} and not matching.get("manualOverride"):
            raise BusinessRuleError("TEMPLATE_NOT_CONFIRMED", "Document template is not confirmed")
        if not matching.get("matchedTemplateId") or not matching.get("matchedTemplateVersionId"):
            raise BusinessRuleError("TEMPLATE_NOT_CONFIRMED", "Document template is not confirmed")
        return matching

    def _validate_preview(self, preview: dict[str, Any]) -> None:
        if preview.get("status") != "preview_ready":
            raise BusinessRuleError("DOCUMENT_PREVIEW_NOT_READY", "Document preview is not ready")
        metadata = preview.get("metadata") or {}
        if metadata.get("requiresOcr"):
            raise BusinessRuleError("DOCUMENT_REQUIRES_OCR", "Document requires OCR, which is out of scope for Fase 13")

    def _validate_template_inputs(
        self,
        document: dict[str, Any],
        template: dict[str, Any],
        version: dict[str, Any],
        fields: list[dict[str, Any]],
        rules: list[dict[str, Any]],
    ) -> None:
        if template.get("status") != "active":
            raise BusinessRuleError("TEMPLATE_NOT_ACTIVE", "Template must be active before extraction")
        if version.get("status") != "published":
            raise BusinessRuleError("TEMPLATE_VERSION_NOT_PUBLISHED", "Template version must be published before extraction")
        if not self._is_template_format_compatible(self._normalized_file_format(document), str(template.get("fileFormat", "")).upper()):
            raise BusinessRuleError("TEMPLATE_FORMAT_INCOMPATIBLE", "Template format is incompatible with document format")
        if not fields:
            raise BusinessRuleError("TEMPLATE_FIELDS_REQUIRED", "Template must define fields before extraction")
        if not rules:
            raise BusinessRuleError("TEMPLATE_EXTRACTION_RULES_REQUIRED", "Template must define extraction rules before extraction")

    async def _build_worker_payload(self, job: ExtractionJob, actor: Principal, correlation_id: str) -> dict[str, Any]:
        document = await self.document_service.get_document(
            job.document_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        preview = await self.document_service.get_preview(
            job.document_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        template = await self.template_service.get_template(
            job.template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        version = await self.template_service.get_template_version(
            job.template_id,
            job.template_version_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        fields = await self.template_service.get_fields(
            job.template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        rules = await self.template_service.get_extraction_rules(
            job.template_id,
            authorization=actor.authorization,
            correlation_id=correlation_id,
        )
        metadata = preview.get("metadata") or {}
        return {
            "extraction_job_id": job.id,
            "correlation_id": correlation_id,
            "document": {
                "document_id": job.document_id,
                "client_id": job.client_id,
                "competence_id": job.competence_id,
                "file_format": job.file_format,
                "original_filename": document.get("originalFilename") or document.get("filename"),
                "storage_bucket": document.get("storageBucket"),
                "storage_key": document.get("storageKey"),
            },
            "preview": {
                "preview_id": metadata.get("previewId"),
                "storage_bucket": metadata.get("storageBucket"),
                "storage_key": metadata.get("storageKey"),
                "preview_json": preview.get("preview"),
                "preview": preview.get("preview"),
            },
            "template": {
                "template_id": job.template_id,
                "template_version_id": job.template_version_id,
                "version_number": version.get("versionNumber") or version.get("version_number"),
                "file_format": template.get("fileFormat"),
                "structure_type": template.get("structureType") or template.get("structure_type"),
                "fields": fields,
                "extraction_rules": rules,
            },
            "options": {
                "strict_mode": False,
                "include_debug": self.settings.app_env != "production",
            },
        }

    def _normalized_file_format(self, document: dict[str, Any]) -> str:
        file_format = str(document.get("fileFormat", "")).upper()
        extension = str(document.get("fileExtension") or "").lower()
        if file_format == "EXCEL" and extension == ".xls":
            return "XLS"
        if file_format == "EXCEL":
            return "XLSX"
        return file_format

    def _is_template_format_compatible(self, document_format: str, template_format: str) -> bool:
        if document_format in {"XLS", "XLSX"}:
            return template_format == "EXCEL"
        return document_format == template_format

    async def _safe_document_status(
        self,
        document_id: str,
        status: str,
        actor: Principal,
        correlation_id: str,
        reason: str,
    ) -> None:
        try:
            await self.document_service.update_document_status(
                document_id,
                status,
                authorization=actor.authorization,
                correlation_id=correlation_id,
                reason=reason,
            )
        except ServiceError:
            return None

    def _publish(
        self,
        event_type: str,
        job: ExtractionJob,
        correlation_id: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "extraction_job_id": job.id,
            "document_id": job.document_id,
            "client_id": job.client_id,
            "competence_id": job.competence_id,
            "template_id": job.template_id,
            "template_version_id": job.template_version_id,
        }
        if extra:
            payload.update(extra)
        self.publisher.publish(
            DomainEvent(
                event_type=event_type,
                payload=payload,
                correlation_id=correlation_id,
                client_id=job.client_id,
                competence_id=job.competence_id,
                document_id=job.document_id,
            )
        )

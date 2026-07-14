import pytest

from app.application.schemas import ExtractionRequest
from app.application.services import ExtractionService
from app.config import get_settings
from app.domain.enums import ExtractionJobStatus
from app.errors import BusinessRuleError, ConflictError, NotFoundError
from app.infrastructure.database.session import SessionLocal
from tests.conftest import OPEN_SESSIONS


DOC_ID = "doc-1"
TPL_ID = "tpl-1"
VER_ID = "ver-1"


def _seed_valid_inputs(fakes, *, file_format: str = "PDF", version_status: str = "published") -> None:
    fakes["document"].documents[DOC_ID] = {
        "documentId": DOC_ID,
        "clientId": "client-1",
        "competenceId": "comp-1",
        "fileFormat": file_format,
        "fileExtension": ".pdf" if file_format == "PDF" else ".xlsx",
        "storageBucket": "cci-documents-original",
        "storageKey": "clients/client-1/doc.pdf",
        "status": "preview_ready",
    }
    fakes["document"].previews[DOC_ID] = {
        "documentId": DOC_ID,
        "status": "preview_ready",
        "preview": {"kind": file_format},
        "metadata": {
            "previewId": "preview-1",
            "requiresOcr": False,
            "storageBucket": "cci-documents-preview",
            "storageKey": "clients/client-1/preview.json",
        },
    }
    fakes["template"].matching[DOC_ID] = {
        "matchingRunId": "match-1",
        "documentId": DOC_ID,
        "status": "matched",
        "matchedTemplateId": TPL_ID,
        "matchedTemplateVersionId": VER_ID,
        "manualOverride": False,
    }
    fakes["template"].templates[TPL_ID] = {
        "templateId": TPL_ID,
        "fileFormat": "PDF" if file_format == "PDF" else "EXCEL",
        "status": "active",
    }
    fakes["template"].versions[(TPL_ID, VER_ID)] = {
        "id": VER_ID,
        "templateId": TPL_ID,
        "status": version_status,
    }
    fakes["template"].fields[TPL_ID] = [{"id": "field-1", "fieldPath": "empresa.cnpj"}]
    fakes["template"].rules[TPL_ID] = [{"id": "rule-1", "fieldId": "field-1", "strategy": "regex"}]


def _service(fakes) -> ExtractionService:
    settings = get_settings()
    session = SessionLocal()
    OPEN_SESSIONS.append(session)
    return ExtractionService(
        session,
        settings,
        fakes["document"],
        fakes["template"],
        fakes["temporal"],
        fakes["dispatcher"],
        fakes["storage"],
        fakes["publisher"],
    )


@pytest.mark.asyncio
async def test_creates_queued_job_for_valid_document(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    service = _service(fakes)

    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    assert job.status == "queued"
    assert job.workflow_id == f"wf-{job.id}"
    assert job.template_id == TPL_ID
    assert fakes["publisher"].events[-1].event_type == "ExtractionRequested"
    assert fakes["document"].statuses[-1] == (DOC_ID, "extraction_pending")


@pytest.mark.asyncio
async def test_rejects_missing_document(fakes, actor) -> None:
    service = _service(fakes)

    with pytest.raises(NotFoundError):
        await service.request_extraction_for_document("missing", ExtractionRequest(), actor, "corr-1")


@pytest.mark.asyncio
async def test_rejects_preview_not_ready(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    fakes["document"].previews[DOC_ID]["status"] = "preview_processing"
    service = _service(fakes)

    with pytest.raises(BusinessRuleError) as exc:
        await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    assert exc.value.code == "DOCUMENT_PREVIEW_NOT_READY"


@pytest.mark.asyncio
async def test_rejects_missing_template_match(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    fakes["template"].matching.clear()
    service = _service(fakes)

    with pytest.raises(BusinessRuleError) as exc:
        await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    assert exc.value.code == "TEMPLATE_NOT_FOUND"


@pytest.mark.asyncio
async def test_rejects_unpublished_template_version(fakes, actor) -> None:
    _seed_valid_inputs(fakes, version_status="draft")
    service = _service(fakes)

    with pytest.raises(BusinessRuleError) as exc:
        await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    assert exc.value.code == "TEMPLATE_VERSION_NOT_PUBLISHED"


def test_chooses_pdf_and_excel_workers(fakes) -> None:
    dispatcher = fakes["dispatcher"]

    assert dispatcher.choose_worker("PDF").worker_name == "pdf-extractor-worker"
    assert dispatcher.choose_worker("XLSX").worker_name == "excel-extractor-worker"


def test_rejects_unsupported_worker_format(fakes) -> None:
    with pytest.raises(BusinessRuleError):
        fakes["dispatcher"].choose_worker("TXT")


@pytest.mark.asyncio
async def test_run_job_once_records_attempt_artifact_and_completion(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    service = _service(fakes)
    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    completed = await service.run_job_once(job.id, actor, "corr-1")

    assert completed.status == "completed"
    assert completed.attempt_count == 1
    assert completed.attempts[0].status == "completed"
    assert completed.artifacts[0].artifact_type == "worker_raw_output"
    assert "ExtractionWorkerDispatched" in [event.event_type for event in fakes["publisher"].events]
    assert "ExtractionCompleted" in [event.event_type for event in fakes["publisher"].events]


@pytest.mark.asyncio
async def test_retry_policy_blocks_retry_above_limit(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    service = _service(fakes)
    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")
    job = service.jobs.get(job.id)
    service.jobs.transition(job, ExtractionJobStatus.STARTING, reason="test", changed_by="test")
    service.jobs.transition(job, ExtractionJobStatus.RUNNING, reason="test", changed_by="test")
    service.jobs.transition(job, ExtractionJobStatus.WAITING_WORKER, reason="test", changed_by="test")
    service.jobs.transition(job, ExtractionJobStatus.FAILED, reason="test", changed_by="test")
    job.attempt_count = job.max_attempts
    service.session.commit()

    with pytest.raises(ConflictError) as exc:
        await service.retry_job(job.id, actor, "corr-1")

    assert exc.value.code == "EXTRACTION_RETRY_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_reprocess_creates_new_job(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    service = _service(fakes)
    first = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(force_reprocess=True), actor, "corr-1")
    second = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(force_reprocess=True), actor, "corr-2")

    assert first.id != second.id

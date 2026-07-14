import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any


SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

database_url = os.environ.get("DATABASE_URL", "")
if not database_url.startswith("postgresql"):
    raise RuntimeError("Extraction Service tests require a PostgreSQL DATABASE_URL")

import pytest
from sqlalchemy import text

from app.config import get_settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.messaging.events import DomainEvent, EventPublisher
from app.infrastructure.temporal.client import WorkflowStartResult
from app.infrastructure.worker_dispatch import WorkerDispatchResult, WorkerDispatcher


class FakeDocumentService:
    def __init__(self) -> None:
        self.documents: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.statuses: list[tuple[str, str]] = []

    async def get_document(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        if document_id not in self.documents:
            from app.errors import NotFoundError

            raise NotFoundError("document")
        return self.documents[document_id]

    async def get_preview(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        if document_id not in self.previews:
            from app.errors import NotFoundError

            raise NotFoundError("document preview")
        return self.previews[document_id]

    async def update_document_status(
        self,
        document_id: str,
        status: str,
        *,
        authorization: str,
        correlation_id: str,
        reason: str | None = None,
    ) -> None:
        self.statuses.append((document_id, status))


class FakeTemplateService:
    def __init__(self) -> None:
        self.matching: dict[str, dict[str, Any]] = {}
        self.templates: dict[str, dict[str, Any]] = {}
        self.versions: dict[tuple[str, str], dict[str, Any]] = {}
        self.fields: dict[str, list[dict[str, Any]]] = {}
        self.rules: dict[str, list[dict[str, Any]]] = {}

    async def get_latest_matching(self, document_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any] | None:
        return self.matching.get(document_id)

    async def get_matching_run(self, matching_run_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        return next(item for item in self.matching.values() if item["matchingRunId"] == matching_run_id)

    async def get_template(self, template_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        return self.templates[template_id]

    async def get_template_version(self, template_id: str, template_version_id: str, *, authorization: str, correlation_id: str) -> dict[str, Any]:
        return self.versions[(template_id, template_version_id)]

    async def get_fields(self, template_id: str, *, authorization: str, correlation_id: str) -> list[dict[str, Any]]:
        return self.fields.get(template_id, [])

    async def get_extraction_rules(self, template_id: str, *, authorization: str, correlation_id: str) -> list[dict[str, Any]]:
        return self.rules.get(template_id, [])


class FakeTemporalClient:
    async def start_extraction_workflow(self, payload: dict[str, Any]) -> WorkflowStartResult:
        return WorkflowStartResult(workflow_id=f"wf-{payload['extraction_job_id']}", workflow_run_id="run-1")

    async def cancel_workflow(self, workflow_id: str) -> None:
        return None


class FakeEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)


class FakeDispatcher(WorkerDispatcher):
    next_raw_output: dict[str, Any] | None = None
    next_status: str = "completed"

    async def dispatch(self, payload: dict[str, Any], selection) -> WorkerDispatchResult:
        return WorkerDispatchResult(
            status=self.next_status,
            raw_output=self.next_raw_output
            or {"worker": selection.worker_name, "payload": {"document_id": payload["document"]["document_id"]}},
        )


class FakeArtifactStorage:
    bucket = "cci-extraction-artifacts"

    def generate_key(self, *, client_id: str, competence_id: str, document_id: str, job_id: str) -> str:
        return f"clients/{client_id}/competences/{competence_id}/documents/{document_id}/extractions/{job_id}/artifact.json"

    def save_json(self, key: str, payload: dict[str, Any]) -> tuple[str, str]:
        self.last_key = key
        self.last_payload = payload
        return self.bucket, "fake-sha256"

    def load_json(self, *, bucket: str, key: str, max_size_bytes: int = 50 * 1024 * 1024) -> dict[str, Any]:
        return getattr(self, "last_payload", {})


OPEN_SESSIONS = []


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    for open_session in OPEN_SESSIONS:
        open_session.close()
    OPEN_SESSIONS.clear()
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE extraction.normalization_runs, extraction.extraction_evidences, "
                "extraction.extracted_field_values, extraction.extracted_array_items, "
                "extraction.extracted_objects, extraction.extraction_results, "
                "extraction.extraction_artifacts, extraction.extraction_attempts, "
                "extraction.extraction_job_status_history, extraction.extraction_jobs CASCADE"
            )
        )
        session.commit()
    yield
    for open_session in OPEN_SESSIONS:
        open_session.close()
    OPEN_SESSIONS.clear()


@pytest.fixture
def actor() -> Principal:
    return Principal(
        id="admin-user",
        name="Admin",
        email="admin@example.com",
        status="ACTIVE",
        roles=("ADMIN",),
        permissions=("documents:read",),
        authorization="Bearer admin",
    )


@pytest.fixture
def fakes() -> dict[str, Any]:
    settings = get_settings()
    return {
        "document": FakeDocumentService(),
        "template": FakeTemplateService(),
        "temporal": FakeTemporalClient(),
        "dispatcher": FakeDispatcher(
            pdf_task_queue=settings.pdf_extractor_worker_task_queue,
            excel_task_queue=settings.excel_extractor_worker_task_queue,
            pdf_worker_url=settings.pdf_extractor_worker_url,
            excel_worker_url=settings.excel_extractor_worker_url,
            timeout_seconds=settings.extractor_worker_timeout_seconds,
        ),
        "storage": FakeArtifactStorage(),
        "publisher": FakeEventPublisher(),
    }

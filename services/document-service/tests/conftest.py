import os
import sys
import json
from collections.abc import Generator
from pathlib import Path


DOCUMENT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOCUMENT_ROOT))

database_url = os.environ.get("DATABASE_URL", "")
if not database_url.startswith("postgresql"):
    raise RuntimeError("Document Service tests require a PostgreSQL DATABASE_URL")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.dependencies import (
    get_client_adapter,
    get_identity_gateway,
    get_parser_worker_client,
    get_storage_client,
)
from app.errors import StorageUnavailableError
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.identity_gateway import Principal
from app.infrastructure.parser_worker import ParserWorkerParseResult
from app.main import app


class FakeIdentityGateway:
    async def authenticate(self, authorization: str, correlation_id: str) -> Principal:
        token = authorization.removeprefix("Bearer ")
        return Principal(
            id=f"{token}-user",
            name=token.title(),
            email=f"{token}@example.com",
            status="ACTIVE",
            roles=("ADMIN",) if token == "admin" else ("OPERATOR",),
            permissions=("client-competencies:read",),
            authorization=authorization,
        )


class FakeClientAdapter:
    async def validate_competence(
        self,
        client_id: str,
        competence_id: str,
        principal: Principal,
        correlation_id: str,
    ) -> None:
        return None

    async def validate_client(
        self,
        client_id: str,
        principal: Principal,
        correlation_id: str,
    ) -> None:
        return None


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.fail_upload = False

    def ensure_bucket(self) -> None:
        return None

    def upload_bytes(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str | None,
        metadata: dict[str, str],
    ) -> None:
        if self.fail_upload:
            raise StorageUnavailableError("simulated storage failure")
        self.objects[(bucket, key)] = content

    def presigned_get_url(self, *, bucket: str, key: str) -> str:
        return f"http://storage.local/{bucket}/{key}"

    def download_bytes(self, *, bucket: str, key: str) -> bytes:
        try:
            return self.objects[(bucket, key)]
        except KeyError as exc:
            raise StorageUnavailableError("missing object") from exc


class FakeParserWorkerClient:
    def __init__(self) -> None:
        self.fail_parse = False
        self.calls = 0

    async def parse(self, request):
        self.calls += 1
        if self.fail_parse:
            raise RuntimeError("invalid_or_corrupt_file")
        preview = {
            "document_id": request.document_id,
            "file_format": request.file_format,
            "parser_version": "test-parser",
            "requires_ocr": False,
            "pages": [
                {
                    "page_number": 1,
                    "width": 595.0,
                    "height": 842.0,
                    "rotation": 0,
                    "text_blocks": [
                        {
                            "block_id": "block-1",
                            "text": "Balancete",
                            "bbox": {"x0": 50.0, "y0": 40.0, "x1": 150.0, "y1": 60.0},
                            "confidence": None,
                            "source": "pdf_text_layer",
                        }
                    ],
                    "lines": [],
                    "tables": [],
                }
            ],
            "summary": {
                "page_count": 1,
                "sheet_count": 0,
                "text_block_count": 1,
                "table_count": 0,
            },
        }
        fake_storage.upload_bytes(
            bucket=request.preview_bucket,
            key=request.preview_storage_key,
            content=json.dumps(preview).encode("utf-8"),
            content_type="application/json",
            metadata={"document_id": request.document_id},
        )
        return ParserWorkerParseResult(
            document_id=request.document_id,
            file_format=request.file_format,
            parser_version="test-parser",
            storage_bucket=request.preview_bucket,
            storage_key=request.preview_storage_key,
            page_count=1,
            sheet_count=0,
            text_block_count=1,
            table_count=0,
            requires_ocr=False,
        )


fake_storage = FakeStorage()
fake_parser_worker = FakeParserWorkerClient()
app.dependency_overrides[get_identity_gateway] = lambda: FakeIdentityGateway()
app.dependency_overrides[get_client_adapter] = lambda: FakeClientAdapter()
app.dependency_overrides[get_storage_client] = lambda: fake_storage
app.dependency_overrides[get_parser_worker_client] = lambda: fake_parser_worker


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    fake_storage.objects.clear()
    fake_storage.fail_upload = False
    fake_parser_worker.fail_parse = False
    fake_parser_worker.calls = 0
    with SessionLocal() as session:
        session.execute(
            text(
                "TRUNCATE document.document_status_history, "
                "document.document_parsing_jobs, document.document_previews, "
                "document.document_upload_batches, document.documents CASCADE"
            )
        )
        session.commit()
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def auth(token: str = "admin") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def upload_pdf(
    client: TestClient,
    *,
    filename: str = "balancete.pdf",
    content: bytes = b"%PDF-1.4 example",
    client_id: str = "client-1",
    competence_id: str = "competence-1",
):
    return client.post(
        "/documents/upload",
        headers=auth(),
        data={"client_id": client_id, "competence_id": competence_id},
        files={"file": (filename, content, "application/pdf")},
    )

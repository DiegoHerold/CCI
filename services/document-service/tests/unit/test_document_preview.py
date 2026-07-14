from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal
from tests.conftest import auth, fake_parser_worker, fake_storage, upload_pdf


def test_request_preview_creates_job_and_updates_status_ready(client: TestClient) -> None:
    document = upload_pdf(client).json()

    response = client.post(f"/documents/{document['documentId']}/preview", headers=auth())

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["documentId"] == document["documentId"]
    assert payload["status"] == "preview_pending"
    assert payload["parsingJobId"]
    assert fake_parser_worker.calls == 1

    status = client.get(f"/documents/{document['documentId']}/preview/status", headers=auth()).json()
    assert status["status"] == "preview_ready"
    assert status["parsingJobId"] == payload["parsingJobId"]

    with SessionLocal() as session:
        job_status = session.scalar(text("SELECT status FROM document.document_parsing_jobs"))
        document_status = session.scalar(text("SELECT status FROM document.documents"))
    assert job_status == "completed"
    assert document_status == "preview_ready"


def test_get_preview_returns_saved_json(client: TestClient) -> None:
    document = upload_pdf(client).json()
    client.post(f"/documents/{document['documentId']}/preview", headers=auth())

    response = client.get(f"/documents/{document['documentId']}/preview", headers=auth())

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "preview_ready"
    assert payload["preview"]["document_id"] == document["documentId"]
    assert payload["preview"]["pages"][0]["text_blocks"][0]["text"] == "Balancete"
    assert any(bucket == "cci-documents-preview" for bucket, _ in fake_storage.objects)


def test_parser_failure_records_preview_failed(client: TestClient) -> None:
    document = upload_pdf(client).json()
    fake_parser_worker.fail_parse = True

    response = client.post(f"/documents/{document['documentId']}/preview", headers=auth())

    assert response.status_code == 200, response.text
    status = client.get(f"/documents/{document['documentId']}/preview/status", headers=auth()).json()
    assert status["status"] == "preview_failed"
    assert "invalid_or_corrupt_file" in status["errorMessage"]

    with SessionLocal() as session:
        job_status = session.scalar(text("SELECT status FROM document.document_parsing_jobs"))
        document_status = session.scalar(text("SELECT status FROM document.documents"))
    assert job_status == "failed"
    assert document_status == "preview_failed"


def test_reprocess_preview_creates_new_job(client: TestClient) -> None:
    document = upload_pdf(client).json()
    first = client.post(f"/documents/{document['documentId']}/preview", headers=auth()).json()
    second = client.post(f"/documents/{document['documentId']}/preview/reprocess", headers=auth()).json()

    assert first["parsingJobId"] != second["parsingJobId"]
    assert fake_parser_worker.calls == 2

    with SessionLocal() as session:
        job_count = session.scalar(text("SELECT count(*) FROM document.document_parsing_jobs"))
        preview_count = session.scalar(text("SELECT count(*) FROM document.document_previews"))
    assert job_count == 2
    assert preview_count == 2

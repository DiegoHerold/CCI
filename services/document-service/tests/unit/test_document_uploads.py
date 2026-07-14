from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal
from tests.conftest import auth, fake_storage, upload_pdf


def make_zip(entries: dict[str, bytes]) -> bytes:
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_upload_valid_file_stores_metadata_and_object(client: TestClient) -> None:
    response = upload_pdf(client)

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "uploaded"
    assert payload["fileFormat"] == "PDF"
    assert payload["isDuplicate"] is False
    assert payload["storageBucket"] == "cci-documents-original"
    assert payload["contentHash"]
    assert len(fake_storage.objects) == 1

    with SessionLocal() as session:
        count = session.scalar(text("SELECT count(*) FROM document.documents"))
    assert count == 1


def test_rejects_invalid_extension(client: TestClient) -> None:
    response = client.post(
        "/documents/upload",
        headers=auth(),
        data={"client_id": "client-1", "competence_id": "competence-1"},
        files={"file": ("malware.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_FILE_TYPE"


def test_hash_duplicate_same_client_competence_returns_original(client: TestClient) -> None:
    first = upload_pdf(client, content=b"same content").json()
    second_response = upload_pdf(client, filename="copy.pdf", content=b"same content")

    assert second_response.status_code == 201
    second = second_response.json()
    assert second["status"] == "duplicate"
    assert second["isDuplicate"] is True
    assert second["documentId"] == first["documentId"]
    assert second["duplicateOfDocumentId"] == first["documentId"]

    with SessionLocal() as session:
        count = session.scalar(text("SELECT count(*) FROM document.documents"))
    assert count == 1


def test_same_hash_allowed_in_different_client_or_competence(client: TestClient) -> None:
    first = upload_pdf(client, content=b"same content").json()
    second = upload_pdf(
        client,
        filename="same.pdf",
        content=b"same content",
        client_id="client-2",
        competence_id="competence-1",
    ).json()

    assert second["status"] == "uploaded"
    assert second["isDuplicate"] is False
    assert second["documentId"] != first["documentId"]


def test_upload_zip_with_valid_and_invalid_files(client: TestClient) -> None:
    archive = make_zip(
        {
            "balancete.pdf": b"%PDF ok",
            "planilha.xlsx": b"xlsx bytes",
            "arquivo.exe": b"bad",
        }
    )
    response = client.post(
        "/documents/upload-zip",
        headers=auth(),
        data={"client_id": "client-1", "competence_id": "competence-1"},
        files={"file": ("lote.zip", archive, "application/zip")},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["totalFiles"] == 3
    assert payload["created"] == 2
    assert payload["rejected"] == 1
    assert payload["errors"][0]["reason"] == "unsupported_file_type"


def test_zip_path_traversal_is_rejected_per_entry(client: TestClient) -> None:
    archive = make_zip({"../evil.pdf": b"%PDF bad", "ok.pdf": b"%PDF ok"})
    response = client.post(
        "/documents/upload-zip",
        headers=auth(),
        data={"client_id": "client-1", "competence_id": "competence-1"},
        files={"file": ("lote.zip", archive, "application/zip")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["created"] == 1
    assert payload["rejected"] == 1
    assert payload["errors"][0]["reason"] == "unsafe_zip_entry"


def test_storage_failure_records_failed_document(client: TestClient) -> None:
    fake_storage.fail_upload = True
    response = upload_pdf(client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DOCUMENT_STORAGE_UNAVAILABLE"
    with SessionLocal() as session:
        statuses = session.scalars(text("SELECT status FROM document.documents")).all()
    assert statuses == ["storage_failed"]


def test_get_list_and_update_status(client: TestClient) -> None:
    created = upload_pdf(client).json()

    fetched = client.get(f"/documents/{created['documentId']}", headers=auth())
    listed = client.get(
        "/documents",
        headers=auth(),
        params={"client_id": "client-1", "competence_id": "competence-1"},
    )
    updated = client.patch(
        f"/documents/{created['documentId']}/status",
        headers=auth(),
        json={"status": "preview_pending", "reason": "parser queued"},
    )

    assert fetched.status_code == 200
    assert listed.json()["total"] == 1
    assert updated.json()["status"] == "preview_pending"


def test_migration_tables_exist(client: TestClient) -> None:
    with SessionLocal() as session:
        tables = set(
            session.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'document'"
                )
            ).all()
        )
    assert {
        "documents",
        "document_previews",
        "document_parsing_jobs",
        "document_upload_batches",
        "document_status_history",
    }.issubset(tables)

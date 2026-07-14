from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal
from tests.conftest import fake_document_service, fake_publisher


def _category(client: TestClient, headers: dict[str, str], slug: str = "balancete") -> dict:
    return client.post(
        "/template-categories",
        headers=headers,
        json={"name": slug.title(), "slug": slug},
    ).json()


def _active_template(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str = "Balancete PDF",
    file_format: str = "PDF",
    structure_type: str = "hierarchical",
    category_id: str | None = None,
) -> dict:
    category = {"id": category_id} if category_id else _category(client, headers, name.lower().replace(" ", "-"))
    template = client.post(
        "/templates",
        headers=headers,
        json={
            "name": name,
            "categoryId": category["id"],
            "fileFormat": file_format,
            "structureType": structure_type,
        },
    ).json()
    field = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=headers,
        json={"fieldPath": "empresa.cnpj", "label": "CNPJ", "fieldType": "cnpj"},
    ).json()
    assert field["id"]
    version = client.post(f"/templates/{template['templateId']}/versions", headers=headers, json={}).json()
    published = client.post(
        f"/templates/{template['templateId']}/versions/{version['id']}/publish",
        headers=headers,
    ).json()
    template["versionId"] = published["versionId"]
    template["categoryId"] = category["id"]
    return template


def _signal(
    client: TestClient,
    headers: dict[str, str],
    template_id: str,
    signal_type: str,
    value: str,
    *,
    weight: float = 10,
    required: bool = False,
    negative: bool = False,
) -> None:
    response = client.post(
        f"/templates/{template_id}/identification-signals",
        headers=headers,
        json={
            "signalType": signal_type,
            "value": value,
            "weight": weight,
            "required": required,
            "negative": negative,
        },
    )
    assert response.status_code == 201


def _pdf_document(document_id: str, text: str, *, requires_ocr: bool = False) -> None:
    fake_document_service.documents[document_id] = {
        "documentId": document_id,
        "clientId": "client-1",
        "competenceId": "competence-2026-07",
        "fileFormat": "PDF",
        "mimeType": "application/pdf",
        "originalFilename": "balancete.pdf",
    }
    fake_document_service.previews[document_id] = {
        "preview": {
            "document_id": document_id,
            "file_format": "PDF",
            "requires_ocr": requires_ocr,
            "pages": [
                {
                    "page_number": 1,
                    "text_blocks": [{"text": text}],
                    "lines": [{"text": text}],
                    "tables": [{"table_id": "t1"}] if text else [],
                }
            ],
            "summary": {"page_count": 1, "sheet_count": 0, "text_block_count": 1 if text else 0, "table_count": 1 if text else 0},
        }
    }


def _excel_document(document_id: str) -> None:
    fake_document_service.documents[document_id] = {
        "documentId": document_id,
        "clientId": "client-1",
        "competenceId": "competence-2026-07",
        "fileFormat": "XLSX",
        "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "originalFilename": "balancete.xlsx",
    }
    fake_document_service.previews[document_id] = {
        "preview": {
            "document_id": document_id,
            "file_format": "XLSX",
            "requires_ocr": False,
            "sheets": [
                {
                    "name": "Balancete",
                    "cells": [{"value": "Saldo Atual"}, {"value": "R$ 1.234,56"}],
                    "detected_headers": [{"values": ["Conta", "Descricao", "Saldo Atual"]}],
                    "detected_tables": [{"table_id": "t1"}],
                }
            ],
            "summary": {"page_count": 0, "sheet_count": 1, "text_block_count": 0, "table_count": 1},
        }
    }


def test_match_pdf_generates_profile_scores_and_publishes_event(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers)
    _signal(client, auth_headers, template["templateId"], "contains_text", "Balancete", required=True)
    _signal(client, auth_headers, template["templateId"], "contains_all_text", "Conta|Saldo Atual")
    _signal(client, auth_headers, template["templateId"], "has_cnpj", "true")
    _signal(client, auth_headers, template["templateId"], "page_count_range", "1-3")
    _pdf_document("doc-pdf-1", "Balancete Conta Saldo Atual CNPJ: 00.000.000/0001-00 31/07/2026 R$ 1.234,56")

    response = client.post(
        "/template-matching/documents/doc-pdf-1/match",
        headers=auth_headers,
        json={"maxCandidates": 5},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "matched"
    assert body["matchedTemplateId"] == template["templateId"]
    assert body["confidence"] == 1.0
    assert body["candidates"][0]["matchedSignals"]
    assert "TemplateMatched" in [event.event_type for event in fake_publisher.events]
    with SessionLocal() as session:
        profile = session.scalar(text("SELECT profile_json FROM template.document_profiles WHERE document_id = 'doc-pdf-1'"))
    assert profile["has_cnpj"] is True
    assert profile["has_tables"] is True


def test_excel_matching_uses_sheet_name_and_column_header(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers, name="Balancete Excel", file_format="XLSX", structure_type="table")
    _signal(client, auth_headers, template["templateId"], "sheet_name", "Balancete", required=True)
    _signal(client, auth_headers, template["templateId"], "column_header", "Saldo Atual")
    _signal(client, auth_headers, template["templateId"], "has_currency_values", "true")
    _excel_document("doc-xlsx-1")

    response = client.post("/template-matching/documents/doc-xlsx-1/match", headers=auth_headers, json={})

    assert response.status_code == 200
    assert response.json()["status"] == "matched"
    assert response.json()["confidence"] == 1.0


def test_filters_by_format_and_requires_published_version(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    pdf = _active_template(client, auth_headers, name="PDF Template", file_format="PDF")
    xlsx = _active_template(client, auth_headers, name="XLSX Template", file_format="XLSX", structure_type="table")
    draft_category = _category(client, auth_headers, "draft-category")
    draft_template = client.post(
        "/templates",
        headers=auth_headers,
        json={
            "name": "Draft PDF",
            "categoryId": draft_category["id"],
            "fileFormat": "PDF",
            "structureType": "text",
        },
    ).json()
    _signal(client, auth_headers, pdf["templateId"], "contains_text", "Balancete")
    _signal(client, auth_headers, xlsx["templateId"], "contains_text", "Balancete")
    _signal(client, auth_headers, draft_template["templateId"], "contains_text", "Balancete")
    _pdf_document("doc-filter-1", "Balancete")

    response = client.post("/template-matching/documents/doc-filter-1/match", headers=auth_headers, json={})

    candidates = response.json()["candidates"]
    assert [item["templateId"] for item in candidates] == [pdf["templateId"]]


def test_not_found_records_weak_candidate_and_event(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers)
    _signal(client, auth_headers, template["templateId"], "contains_text", "Extrato", weight=10)
    _pdf_document("doc-not-found-1", "Balancete")

    response = client.post("/template-matching/documents/doc-not-found-1/match", headers=auth_headers, json={})

    assert response.status_code == 200
    assert response.json()["status"] == "not_found"
    assert response.json()["candidates"][0]["score"] == 0
    assert "TemplateNotFound" in [event.event_type for event in fake_publisher.events]


def test_ambiguous_when_top_candidates_are_close(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = _active_template(client, auth_headers, name="Balancete A")
    second = _active_template(client, auth_headers, name="Balancete B")
    _signal(client, auth_headers, first["templateId"], "contains_text", "Balancete")
    _signal(client, auth_headers, second["templateId"], "contains_text", "Balancete")
    _pdf_document("doc-ambiguous-1", "Balancete")

    response = client.post("/template-matching/documents/doc-ambiguous-1/match", headers=auth_headers, json={})

    assert response.status_code == 200
    assert response.json()["status"] == "ambiguous"
    assert len(response.json()["candidates"]) == 2
    assert "TemplateAmbiguous" in [event.event_type for event in fake_publisher.events]


def test_required_missing_eliminates_and_negative_signal_penalizes(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers)
    _signal(client, auth_headers, template["templateId"], "contains_text", "Balancete", required=True)
    _signal(client, auth_headers, template["templateId"], "not_contains_text", "Extrato", negative=True)
    _pdf_document("doc-negative-1", "Balancete Extrato")

    response = client.post("/template-matching/documents/doc-negative-1/match", headers=auth_headers, json={})

    candidate = response.json()["candidates"][0]
    assert response.json()["status"] == "not_found"
    assert candidate["negativeMatches"]


def test_manual_confirmation_creates_matched_override(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers)

    response = client.post(
        "/template-matching/documents/doc-manual-1/confirm",
        headers=auth_headers,
        json={
            "templateId": template["templateId"],
            "templateVersionId": template["versionId"],
            "reason": "Selecionado apos revisao humana",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "matched"
    assert response.json()["manualOverride"] is True
    assert response.json()["confidence"] == 1.0
    assert "TemplateManuallyConfirmed" in [event.event_type for event in fake_publisher.events]


def test_missing_preview_returns_404(client: TestClient, auth_headers: dict[str, str]) -> None:
    fake_document_service.documents["doc-without-preview"] = {"documentId": "doc-without-preview", "fileFormat": "PDF"}

    response = client.post("/template-matching/documents/doc-without-preview/match", headers=auth_headers, json={})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_PREVIEW_NOT_FOUND"


def test_requires_ocr_document_without_text_can_match_structure_hint(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    template = _active_template(client, auth_headers, name="PDF OCR", structure_type="text")
    _signal(client, auth_headers, template["templateId"], "structure_hint", "requires_ocr", required=True)
    _pdf_document("doc-ocr-1", "", requires_ocr=True)

    response = client.post("/template-matching/documents/doc-ocr-1/match", headers=auth_headers, json={})

    assert response.status_code == 200
    assert response.json()["status"] == "matched"

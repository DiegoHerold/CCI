from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.database.session import SessionLocal
from tests.conftest import fake_publisher


def test_create_category_and_reject_duplicate_slug(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    first = client.post(
        "/template-categories",
        headers=auth_headers,
        json={"name": "Balancete", "slug": "balancete"},
    )
    duplicate = client.post(
        "/template-categories",
        headers=auth_headers,
        json={"name": "Balancete 2", "slug": "balancete"},
    )
    listed = client.get("/template-categories", headers=auth_headers)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "TEMPLATE_CATEGORY_SLUG_EXISTS"
    assert listed.json()["items"][0]["slug"] == "balancete"


def test_create_template_and_filter_by_category_and_format(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    created = create_template()

    response = client.get(
        "/templates",
        headers=auth_headers,
        params={"category_id": created["categoryId"], "file_format": "PDF"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["templateId"] == created["templateId"]


def test_reject_template_without_valid_category(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/templates",
        headers=auth_headers,
        json={
            "name": "Sem categoria",
            "categoryId": "missing",
            "fileFormat": "PDF",
            "structureType": "text",
        },
    )

    assert response.status_code == 404


def test_create_fields_and_reject_duplicate_path(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    simple = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=auth_headers,
        json={
            "fieldPath": "empresa.cnpj",
            "label": "CNPJ da empresa",
            "fieldType": "cnpj",
            "isRequired": True,
        },
    )
    array = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=auth_headers,
        json={
            "fieldPath": "contas[]",
            "label": "Contas contabeis",
            "fieldType": "array",
            "isRequired": True,
            "isRepeated": True,
            "isArray": True,
        },
    )
    duplicate = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=auth_headers,
        json={
            "fieldPath": "empresa.cnpj",
            "label": "CNPJ duplicado",
            "fieldType": "cnpj",
        },
    )

    assert simple.status_code == 201
    assert array.status_code == 201
    assert array.json()["isArray"] is True
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "TEMPLATE_FIELD_PATH_EXISTS"


def test_reject_child_field_without_parent(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    response = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=auth_headers,
        json={
            "parentFieldId": "missing",
            "fieldPath": "contas[].codigo",
            "label": "Codigo",
            "fieldType": "text",
        },
    )

    assert response.status_code == 404


def test_create_identification_signal(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    response = client.post(
        f"/templates/{template['templateId']}/identification-signals",
        headers=auth_headers,
        json={
            "signalType": "contains_text",
            "value": "Balancete",
            "weight": 10,
            "required": True,
            "negative": False,
        },
    )
    listed = client.get(
        f"/templates/{template['templateId']}/identification-signals",
        headers=auth_headers,
    )

    assert response.status_code == 201
    assert listed.json()["items"][0]["signalType"] == "contains_text"


def _create_field(client: TestClient, headers: dict[str, str], template_id: str) -> dict:
    return client.post(
        f"/templates/{template_id}/fields",
        headers=headers,
        json={
            "fieldPath": "empresa.cnpj",
            "label": "CNPJ da empresa",
            "fieldType": "cnpj",
            "isRequired": True,
        },
    ).json()


def test_create_pdf_and_excel_annotations(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    field = _create_field(client, auth_headers, template["templateId"])
    pdf = client.post(
        f"/templates/{template['templateId']}/annotations",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "documentId": "document-1",
            "sourcePreviewId": "preview-1",
            "annotationType": "pdf_text_block",
            "selectedText": "CNPJ: 00.000.000/0001-00",
            "selectionPayload": {
                "selection_type": "pdf_text_block",
                "page_number": 1,
                "bbox": {"x0": 50, "y0": 80, "x1": 250, "y1": 100},
            },
        },
    )
    excel = client.post(
        f"/templates/{template['templateId']}/annotations",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "documentId": "document-2",
            "annotationType": "excel_column",
            "selectionPayload": {
                "selection_type": "excel_column",
                "sheet_name": "Balancete",
                "column": 6,
                "column_letter": "F",
                "header": "Saldo Atual",
            },
        },
    )

    assert pdf.status_code == 201
    assert excel.status_code == 201
    assert excel.json()["annotationType"] == "excel_column"


def test_reject_annotation_without_valid_field(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    response = client.post(
        f"/templates/{template['templateId']}/annotations",
        headers=auth_headers,
        json={
            "fieldId": "missing",
            "documentId": "document-1",
            "annotationType": "pdf_area",
            "selectionPayload": {"selection_type": "pdf_area"},
        },
    )

    assert response.status_code == 404


def test_create_extraction_rule(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    field = _create_field(client, auth_headers, template["templateId"])
    response = client.post(
        f"/templates/{template['templateId']}/extraction-rules",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "strategy": "find_near_label",
            "config": {"label": "CNPJ", "position": "right", "max_distance": 200},
        },
    )

    assert response.status_code == 201
    assert response.json()["strategy"] == "find_near_label"


def test_reject_invalid_extraction_strategy(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    field = _create_field(client, auth_headers, template["templateId"])
    response = client.post(
        f"/templates/{template['templateId']}/extraction-rules",
        headers=auth_headers,
        json={"fieldId": field["id"], "strategy": "execute_python", "config": {}},
    )

    assert response.status_code == 422


def test_create_publish_and_snapshot_version(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    field = _create_field(client, auth_headers, template["templateId"])
    client.post(
        f"/templates/{template['templateId']}/extraction-rules",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "strategy": "find_near_label",
            "config": {"label": "CNPJ"},
        },
    )
    version = client.post(
        f"/templates/{template['templateId']}/versions",
        headers=auth_headers,
        json={},
    )
    published = client.post(
        f"/templates/{template['templateId']}/versions/{version.json()['id']}/publish",
        headers=auth_headers,
    )
    detail = client.get(f"/templates/{template['templateId']}", headers=auth_headers)

    assert version.status_code == 201
    assert published.status_code == 200
    assert published.json()["status"] == "published"
    assert detail.json()["activeVersionId"] == version.json()["id"]
    version_detail = client.get(
        f"/templates/{template['templateId']}/versions/{version.json()['id']}",
        headers=auth_headers,
    ).json()
    assert version_detail["snapshot"]["fields"][0]["field_path"] == "empresa.cnpj"
    assert version_detail["snapshot"]["extraction_rules"][0]["strategy"] == "find_near_label"


def test_published_version_is_immutable_for_direct_annotation_link(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template = create_template()
    field = _create_field(client, auth_headers, template["templateId"])
    version = client.post(
        f"/templates/{template['templateId']}/versions",
        headers=auth_headers,
        json={},
    ).json()
    client.post(
        f"/templates/{template['templateId']}/versions/{version['id']}/publish",
        headers=auth_headers,
    )
    response = client.post(
        f"/templates/{template['templateId']}/annotations",
        headers=auth_headers,
        json={
            "templateVersionId": version["id"],
            "fieldId": field["id"],
            "documentId": "document-1",
            "annotationType": "pdf_area",
            "selectionPayload": {"selection_type": "pdf_area"},
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "TEMPLATE_VERSION_PUBLISHED_IMMUTABLE"


def test_publisher_captures_template_events(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    create_template()

    event_types = [event.event_type for event in fake_publisher.events]
    assert "TemplateCategoryCreated" in event_types
    assert "TemplateCreated" in event_types


def test_migration_tables_exist(client: TestClient) -> None:
    with SessionLocal() as session:
        tables = set(
            session.scalars(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'template'"
                )
            ).all()
        )
    assert {
        "categories",
        "templates",
        "template_versions",
        "template_fields",
        "identification_signals",
        "template_annotations",
        "extraction_rules",
    }.issubset(tables)

from fastapi.testclient import TestClient


def _template_with_field(client: TestClient, headers: dict[str, str], create_template) -> tuple[dict, dict]:
    template = create_template()
    field = client.post(
        f"/templates/{template['templateId']}/fields",
        headers=headers,
        json={
            "fieldPath": "empresa.cnpj",
            "label": "CNPJ",
            "fieldType": "cnpj",
            "isRequired": True,
        },
    ).json()
    return template, field


def test_builder_state_returns_template_components(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template, field = _template_with_field(client, auth_headers, create_template)
    client.post(
        f"/templates/{template['templateId']}/identification-signals",
        headers=auth_headers,
        json={"signalType": "contains_text", "value": "Balancete", "weight": 10},
    )

    response = client.get(f"/templates/{template['templateId']}/builder-state", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["template"]["templateId"] == template["templateId"]
    assert body["fields"][0]["id"] == field["id"]
    assert body["identificationSignals"][0]["signalType"] == "contains_text"
    assert body["annotations"] == []


def test_create_pdf_annotation_with_suggested_find_near_label_rule(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template, field = _template_with_field(client, auth_headers, create_template)

    response = client.post(
        f"/templates/{template['templateId']}/annotations/with-rule",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "documentId": "document-1",
            "annotationType": "pdf_text_block",
            "selectedText": "CNPJ: 00.000.000/0001-00",
            "selectionPayload": {
                "selection_type": "pdf_text_block",
                "document_id": "document-1",
                "page_number": 1,
                "text": "CNPJ: 00.000.000/0001-00",
                "bbox": {"x0": 50, "y0": 80, "x1": 250, "y1": 100},
                "source": "preview",
            },
            "generateRule": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["annotation"]["annotationType"] == "pdf_text_block"
    assert body["extractionRule"]["strategy"] == "find_near_label"
    assert body["extractionRule"]["config"]["label"] == "CNPJ"
    assert body["extractionRule"]["createdFromAnnotationId"] == body["annotation"]["id"]


def test_create_excel_column_annotation_with_header_rule(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template, field = _template_with_field(client, auth_headers, create_template)

    response = client.post(
        f"/templates/{template['templateId']}/annotations/with-rule",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "documentId": "document-2",
            "annotationType": "excel_column",
            "selectedText": "Saldo Atual",
            "selectionPayload": {
                "selection_type": "excel_column",
                "document_id": "document-2",
                "sheet_name": "Balancete",
                "sheet_index": 0,
                "column": 6,
                "column_letter": "F",
                "header": "Saldo Atual",
                "source": "user_column_selection",
            },
            "generateRule": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["extractionRule"]["strategy"] == "excel_column_by_header"
    assert body["extractionRule"]["config"]["header_aliases"] == ["Saldo Atual", "Saldo Atual"]


def test_update_annotation_metadata(
    client: TestClient, auth_headers: dict[str, str], create_template
) -> None:
    template, field = _template_with_field(client, auth_headers, create_template)
    created = client.post(
        f"/templates/{template['templateId']}/annotations",
        headers=auth_headers,
        json={
            "fieldId": field["id"],
            "documentId": "document-1",
            "annotationType": "pdf_area",
            "selectionPayload": {"selection_type": "pdf_area", "page_number": 1},
        },
    ).json()

    response = client.patch(
        f"/templates/{template['templateId']}/annotations/{created['id']}",
        headers=auth_headers,
        json={"selectedText": "Area revisada"},
    )

    assert response.status_code == 200
    assert response.json()["selectedText"] == "Area revisada"

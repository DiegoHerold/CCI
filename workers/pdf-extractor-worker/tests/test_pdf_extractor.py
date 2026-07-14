from app.extractor import extract_pdf


def _preview():
    return {
        "file_format": "PDF",
        "pages": [
            {
                "page_number": 1,
                "lines": [
                    {
                        "text": "CNPJ: 00.000.000/0001-00",
                        "bbox": {"x0": 40, "y0": 40, "x1": 210, "y1": 52},
                        "tokens": [
                            {"text": "CNPJ:", "bbox": {"x0": 40, "y0": 40, "x1": 75, "y1": 52}},
                            {"text": "00.000.000/0001-00", "bbox": {"x0": 82, "y0": 40, "x1": 210, "y1": 52}},
                        ],
                    },
                    {
                        "text": "1 ATIVO 100000,00",
                        "bbox": {"x0": 30, "y0": 100, "x1": 240, "y1": 112},
                        "tokens": [
                            {"text": "1", "bbox": {"x0": 30, "y0": 100, "x1": 45, "y1": 112}},
                            {"text": "ATIVO", "bbox": {"x0": 90, "y0": 100, "x1": 150, "y1": 112}},
                            {"text": "100000,00", "bbox": {"x0": 450, "y0": 100, "x1": 520, "y1": 112}},
                        ],
                    },
                    {
                        "text": "1.1 Caixa 15000,00",
                        "bbox": {"x0": 30, "y0": 120, "x1": 240, "y1": 132},
                        "tokens": [
                            {"text": "1.1", "bbox": {"x0": 30, "y0": 120, "x1": 70, "y1": 132}},
                            {"text": "Caixa", "bbox": {"x0": 100, "y0": 120, "x1": 170, "y1": 132}},
                            {"text": "15000,00", "bbox": {"x0": 450, "y0": 120, "x1": 520, "y1": 132}},
                        ],
                    },
                ],
                "text_blocks": [],
            }
        ],
    }


def _request(rules):
    return {
        "extraction_job_id": "job-1",
        "correlation_id": "corr-1",
        "document": {"document_id": "doc-1", "file_format": "PDF"},
        "preview": {"preview_json": _preview()},
        "template": {"template_id": "tpl-1", "template_version_id": "ver-1", "extraction_rules": rules},
        "options": {},
    }


def test_find_near_label_extracts_with_pdf_evidence():
    result = extract_pdf(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_id": "field-1",
                    "field_path": "empresa.cnpj",
                    "strategy": "find_near_label",
                    "config": {"label": "CNPJ", "position": "right"},
                }
            ]
        )
    )

    field = result["raw_output"]["raw_extracted_fields"][0]
    assert result["status"] == "completed"
    assert field["raw_value"] == "00.000.000/0001-00"
    assert field["evidence"]["evidence_type"] == "pdf"
    assert field["evidence"]["page_number"] == 1


def test_fixed_bbox_and_regex_extract_fields():
    result = extract_pdf(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_path": "empresa.cnpj",
                    "strategy": "fixed_bbox",
                    "config": {"page_number": 1, "bbox": {"x0": 80, "y0": 38, "x1": 220, "y1": 54}},
                },
                {
                    "id": "rule-2",
                    "field_path": "empresa.cnpj_regex",
                    "strategy": "regex_from_text",
                    "config": {"pattern": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"},
                },
            ]
        )
    )

    values = [field["raw_value"] for field in result["raw_output"]["raw_extracted_fields"]]
    assert "00.000.000/0001-00" in values


def test_pdf_table_column_and_hierarchy_outputs_arrays():
    result = extract_pdf(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_path": "contas[]",
                    "strategy": "pdf_area_table",
                    "config": {
                        "page_number": 1,
                        "bbox": {"x0": 20, "y0": 90, "x1": 560, "y1": 140},
                        "columns": [
                            {"field_path": "contas[].codigo", "x0": 20, "x1": 80},
                            {"field_path": "contas[].descricao", "x0": 80, "x1": 250},
                            {"field_path": "contas[].saldo_atual", "x0": 430, "x1": 540},
                        ],
                    },
                },
                {
                    "id": "rule-2",
                    "field_path": "contas[].saldo_atual",
                    "strategy": "pdf_column_by_x_position",
                    "config": {"page_number": 1, "bbox": {"x0": 20, "y0": 90, "x1": 560, "y1": 140}, "x0": 430, "x1": 540},
                },
                {
                    "id": "rule-3",
                    "field_path": "contas[]",
                    "strategy": "hierarchical_lines",
                    "config": {"page_number": 1},
                },
            ]
        )
    )

    objects = result["raw_output"]["raw_extracted_objects"]
    assert objects[0]["items"][0]["values"]["codigo"]["raw_value"] == "1"
    assert objects[1]["items"][1]["values"]["nivel"]["raw_value"] == 2
    assert result["raw_output"]["raw_extracted_fields"][0]["raw_value"] == ["100000,00", "15000,00"]


def test_returns_not_found_and_invalid_rule_error():
    result = extract_pdf(
        _request(
            [
                {"id": "rule-1", "field_path": "empresa.ie", "strategy": "find_near_label", "config": {"label": "IE"}},
                {"id": "rule-2", "field_path": "empresa.bad", "strategy": "regex_from_text", "config": {"pattern": "["}},
            ]
        )
    )

    assert result["status"] == "completed_with_warnings"
    assert result["raw_output"]["raw_extracted_fields"][0]["status"] == "not_found"
    assert "invalid_rule_config" in result["errors"]

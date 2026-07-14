from app.extractor import extract_excel


def _preview():
    cells = [
        {"address": "A1", "row": 1, "column": 1, "column_letter": "A", "value": "Conta"},
        {"address": "B1", "row": 1, "column": 2, "column_letter": "B", "value": "Descricao"},
        {"address": "C1", "row": 1, "column": 3, "column_letter": "C", "value": "Saldo Atual"},
        {"address": "A2", "row": 2, "column": 1, "column_letter": "A", "value": "1"},
        {"address": "B2", "row": 2, "column": 2, "column_letter": "B", "value": "ATIVO"},
        {"address": "C2", "row": 2, "column": 3, "column_letter": "C", "value": "100000,00"},
        {"address": "A3", "row": 3, "column": 1, "column_letter": "A", "value": "1.1"},
        {"address": "B3", "row": 3, "column": 2, "column_letter": "B", "value": "Caixa"},
        {"address": "C3", "row": 3, "column": 3, "column_letter": "C", "value": "15000,00"},
        {"address": "A4", "row": 4, "column": 1, "column_letter": "A", "value": ""},
        {"address": "B4", "row": 4, "column": 2, "column_letter": "B", "value": ""},
        {"address": "C4", "row": 4, "column": 3, "column_letter": "C", "value": ""},
        {"address": "E2", "row": 2, "column": 5, "column_letter": "E", "value": "00.000.000/0001-00"},
    ]
    return {
        "file_format": "XLSX",
        "sheets": [
            {
                "name": "Balancete",
                "index": 0,
                "max_row": 4,
                "max_column": 5,
                "cells": cells,
                "detected_headers": [{"row": 1, "values": ["Conta", "Descricao", "Saldo Atual"], "confidence": 0.9}],
                "detected_tables": [{"range": "A1:C4", "header_row": 1, "start_row": 2, "end_row": 4, "confidence": 0.9}],
                "merged_cells": [{"range": "E2:E2"}],
            }
        ],
    }


def _request(rules):
    return {
        "extraction_job_id": "job-1",
        "correlation_id": "corr-1",
        "document": {"document_id": "doc-1", "file_format": "XLSX"},
        "preview": {"preview_json": _preview()},
        "template": {"template_id": "tpl-1", "template_version_id": "ver-1", "extraction_rules": rules},
        "options": {},
    }


def test_excel_cell_address_extracts_with_evidence():
    result = extract_excel(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_path": "empresa.cnpj",
                    "strategy": "excel_cell_address",
                    "config": {"sheet_name": "Balancete", "cell": "E2"},
                }
            ]
        )
    )

    field = result["raw_output"]["raw_extracted_fields"][0]
    assert result["status"] == "completed"
    assert field["raw_value"] == "00.000.000/0001-00"
    assert field["evidence"]["evidence_type"] == "excel"
    assert field["evidence"]["cell_range"] == "E2:E2"


def test_excel_column_by_header_extracts_values_and_warns_for_ambiguous_header():
    preview = _preview()
    preview["sheets"][0]["cells"].append({"address": "D1", "row": 1, "column": 4, "column_letter": "D", "value": "Saldo Atual"})
    request = _request(
        [
            {
                "id": "rule-1",
                "field_path": "contas[].saldo_atual",
                "strategy": "excel_column_by_header",
                "config": {"sheet_name": "Balancete", "header_aliases": ["Saldo Atual"], "start_row": 2},
            }
        ]
    )
    request["preview"]["preview_json"] = preview

    result = extract_excel(request)

    field = result["raw_output"]["raw_extracted_fields"][0]
    assert field["raw_value"][0]["raw_value"] == "100000,00"
    assert any(warning.startswith("ambiguous_header") for warning in result["warnings"])


def test_excel_range_table_extracts_list_with_hierarchy_and_ignores_empty_rows():
    result = extract_excel(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_path": "contas[]",
                    "strategy": "excel_range_table",
                    "config": {
                        "sheet_name": "balancete",
                        "range": "A1:C4",
                        "header_row": 1,
                        "start_row": 2,
                        "columns": [
                            {"header": "Conta", "field_path": "contas[].codigo"},
                            {"header": "Descricao", "field_path": "contas[].descricao"},
                            {"header": "Saldo Atual", "field_path": "contas[].saldo_atual"},
                        ],
                        "hierarchy": {"enabled": True, "level_from": "account_code", "account_code_field": "contas[].codigo"},
                    },
                }
            ]
        )
    )

    obj = result["raw_output"]["raw_extracted_objects"][0]
    assert obj["items"][1]["values"]["nivel"]["raw_value"] == 2
    assert len(obj["items"]) == 2
    assert any(warning.startswith("empty_row_ignored") for warning in result["warnings"])


def test_excel_sheet_by_name_and_missing_sheet_error():
    found = extract_excel(
        _request(
            [
                {
                    "id": "rule-1",
                    "field_path": "documento.aba",
                    "strategy": "excel_sheet_by_name",
                    "config": {"sheet_aliases": ["BALANCETE"]},
                }
            ]
        )
    )
    missing = extract_excel(
        _request(
            [
                {
                    "id": "rule-2",
                    "field_path": "documento.aba",
                    "strategy": "excel_sheet_by_name",
                    "config": {"sheet_name": "Razao"},
                }
            ]
        )
    )

    assert found["raw_output"]["raw_extracted_fields"][0]["raw_value"] == "Balancete"
    assert missing["status"] == "failed"
    assert "sheet_not_found" in missing["errors"]

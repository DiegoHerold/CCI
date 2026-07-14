import pytest

from app.application.schemas import ExtractionRequest
from app.application.services import ExtractionService
from app.config import get_settings
from app.infrastructure.database.session import SessionLocal
from tests.conftest import OPEN_SESSIONS
from tests.unit.test_extraction_service import DOC_ID, TPL_ID, VER_ID, _seed_valid_inputs


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


def _raw_output() -> dict:
    return {
        "extraction_job_id": "job-1",
        "status": "completed",
        "worker_type": "pdf-extractor-worker",
        "template_id": TPL_ID,
        "template_version_id": VER_ID,
        "document_id": DOC_ID,
        "raw_extracted_fields": [
            {
                "field_id": "field-cnpj",
                "field_path": "empresa.cnpj",
                "raw_value": "11.222.333/0001-81",
                "data_type": "cnpj",
                "confidence": 0.92,
                "status": "extracted",
                "evidence": {
                    "evidence_type": "pdf",
                    "document_id": DOC_ID,
                    "page_number": 1,
                    "bbox": {"x0": 10, "y0": 20, "x1": 100, "y1": 40},
                    "source_text": "CNPJ: 11.222.333/0001-81",
                    "rule_id": "rule-1",
                    "rule_strategy": "find_near_label",
                    "confidence": 0.92,
                },
            }
        ],
        "raw_extracted_objects": [
            {
                "field_path": "contas[]",
                "field_type": "array",
                "items": [
                    {
                        "index": 0,
                        "values": {
                            "codigo": {
                                "raw_value": "1.1.01",
                                "confidence": 0.9,
                                "status": "extracted",
                                "evidence": {
                                    "evidence_type": "excel",
                                    "document_id": DOC_ID,
                                    "sheet_name": "Balancete",
                                    "cell_range": "A2:A2",
                                    "source_value": "1.1.01",
                                    "rule_id": "rule-2",
                                    "rule_strategy": "excel_range_table",
                                    "confidence": 0.9,
                                },
                            },
                            "saldo_atual": {
                                "raw_value": "1.234,56",
                                "confidence": 0.91,
                                "status": "extracted",
                                "evidence": {
                                    "evidence_type": "excel",
                                    "document_id": DOC_ID,
                                    "sheet_name": "Balancete",
                                    "cell_range": "C2:C2",
                                    "source_value": "1.234,56",
                                    "rule_id": "rule-2",
                                    "rule_strategy": "excel_range_table",
                                    "confidence": 0.91,
                                },
                            },
                        },
                    }
                ],
            }
        ],
        "warnings": [],
        "errors": [],
    }


def _seed_result_fields(fakes) -> None:
    fakes["template"].fields[TPL_ID] = [
        {"id": "field-cnpj", "fieldPath": "empresa.cnpj", "fieldType": "cnpj", "isRequired": True},
        {"id": "field-conta", "fieldPath": "contas[].codigo", "fieldType": "account_code", "isRequired": True},
        {"id": "field-saldo", "fieldPath": "contas[].saldo_atual", "fieldType": "money", "isRequired": False},
    ]


@pytest.mark.asyncio
async def test_run_job_once_saves_result_fields_arrays_and_evidence(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    _seed_result_fields(fakes)
    fakes["dispatcher"].next_raw_output = _raw_output()
    service = _service(fakes)
    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    completed = await service.run_job_once(job.id, actor, "corr-1")
    result = service.get_result_for_job(job.id)
    fields = service.list_result_fields(result.id)
    objects = service.list_result_objects(result.id)
    array_items = service.list_array_items(result.id, "contas[]")
    cnpj = next(field for field in fields if field.field_path == "empresa.cnpj")
    evidence = service.list_field_evidence(cnpj.id)

    assert completed.status == "completed"
    assert result.status == "completed"
    assert result.field_count == 3
    assert result.normalized_count == 3
    assert cnpj.raw_value == "11.222.333/0001-81"
    assert cnpj.normalized_value == "11222333000181"
    assert objects[0].field_path == "contas[]"
    assert array_items[0].item_index == 0
    assert evidence[0].evidence_type == "pdf"
    assert "ExtractionResultsSaved" in [event.event_type for event in fakes["publisher"].events]


@pytest.mark.asyncio
async def test_requires_review_when_required_field_not_found(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    _seed_result_fields(fakes)
    raw_output = _raw_output()
    raw_output["raw_extracted_fields"][0]["status"] = "not_found"
    raw_output["raw_extracted_fields"][0]["raw_value"] = None
    raw_output["raw_extracted_fields"][0]["evidence"] = None
    fakes["dispatcher"].next_raw_output = raw_output
    service = _service(fakes)
    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")

    completed = await service.run_job_once(job.id, actor, "corr-1")
    result = service.get_result_for_job(job.id)

    assert completed.status == "requires_review"
    assert result.status == "requires_review"
    assert result.requires_review_count >= 1
    assert "ExtractionRequiresReview" in [event.event_type for event in fakes["publisher"].events]


@pytest.mark.asyncio
async def test_reprocess_normalization_creates_new_result_from_raw_artifact(fakes, actor) -> None:
    _seed_valid_inputs(fakes)
    _seed_result_fields(fakes)
    fakes["dispatcher"].next_raw_output = _raw_output()
    service = _service(fakes)
    job = await service.request_extraction_for_document(DOC_ID, ExtractionRequest(), actor, "corr-1")
    await service.run_job_once(job.id, actor, "corr-1")

    reprocessed = await service.reprocess_normalization(job.id, actor, "corr-2", "normalizer update")

    assert reprocessed.extraction_job_id == job.id
    assert reprocessed.field_count == 3

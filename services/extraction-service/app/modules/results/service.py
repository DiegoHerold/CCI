from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import Settings
from app.domain.enums import (
    ExtractedFieldStatus,
    ExtractionResultStatus,
    NormalizationRunStatus,
)
from app.infrastructure.database.models import ExtractionJob, ExtractionResult
from app.infrastructure.database.repositories import ExtractionResultRepository
from app.modules.confidence.service import ConfidenceService
from app.modules.normalization.normalizers import ValueNormalizer


REVIEW_STATUSES = {
    ExtractedFieldStatus.REQUIRES_REVIEW.value,
    ExtractedFieldStatus.NORMALIZATION_FAILED.value,
    ExtractedFieldStatus.LOW_CONFIDENCE.value,
    ExtractedFieldStatus.EVIDENCE_MISSING.value,
    ExtractedFieldStatus.AMBIGUOUS.value,
}


@dataclass(frozen=True)
class ResultProcessingOutcome:
    result: ExtractionResult
    status: ExtractionResultStatus


class ExtractionResultService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.repository = ExtractionResultRepository(session)
        self.normalizer = ValueNormalizer()
        self.confidence = ConfidenceService(settings.normalization_low_confidence_threshold)

    def process_worker_output(self, *, job: ExtractionJob, raw_output: dict[str, Any], fields: list[dict[str, Any]]) -> ResultProcessingOutcome:
        run = self.repository.create_run(job=job, status=NormalizationRunStatus.STARTED.value)
        run.started_at = datetime.now(UTC)
        field_definitions = self._field_definitions(fields)
        raw_fields = list(raw_output.get("raw_extracted_fields") or [])
        raw_objects = list(raw_output.get("raw_extracted_objects") or [])
        if len(raw_fields) > self.settings.normalization_max_fields_per_result:
            run.status = NormalizationRunStatus.FAILED.value
            run.finished_at = datetime.now(UTC)
            run.error_message = "normalization field limit exceeded"
            self.session.flush()
            raise ValueError("normalization field limit exceeded")

        pending_fields: list[dict[str, Any]] = []
        object_specs: list[dict[str, Any]] = []
        array_items: list[dict[str, Any]] = []
        object_specs.extend(raw_objects)
        pending_fields.extend(raw_fields)

        for raw_object in raw_objects:
            if str(raw_object.get("field_type")) != "array":
                continue
            items = list(raw_object.get("items") or [])
            if len(items) > self.settings.normalization_max_array_items:
                run.status = NormalizationRunStatus.FAILED.value
                run.finished_at = datetime.now(UTC)
                run.error_message = "normalization array item limit exceeded"
                self.session.flush()
                raise ValueError("normalization array item limit exceeded")
            for item in items:
                array_items.append(
                    {
                        "array_field_path": raw_object.get("field_path"),
                        "item_index": int(item.get("index", len(array_items))),
                        "values": item.get("values") or {},
                    }
                )

        normalized_previews = [
            self._normalize_raw_field(raw_field, field_definitions, item_index=None)
            for raw_field in pending_fields
        ]
        for array_item in array_items:
            for key, value in array_item["values"].items():
                path = self._array_child_path(array_item["array_field_path"], key, field_definitions)
                normalized_previews.append(
                    self._normalize_raw_field(
                        {
                            "field_path": path,
                            "field_id": None,
                            "data_type": None,
                            "raw_value": value.get("raw_value") if isinstance(value, dict) else value,
                            "confidence": value.get("confidence", 0.0) if isinstance(value, dict) else 0.0,
                            "status": value.get("status", "extracted") if isinstance(value, dict) else "extracted",
                            "evidence": value.get("evidence") if isinstance(value, dict) else None,
                        },
                        field_definitions,
                        item_index=array_item["item_index"],
                    )
                )

        field_count = len(normalized_previews)
        normalized_count = sum(1 for item in normalized_previews if item["status"] == ExtractedFieldStatus.NORMALIZED.value)
        requires_review_count = sum(1 for item in normalized_previews if item["status"] in REVIEW_STATUSES)
        error_count = len(raw_output.get("errors") or [])
        warning_count = len(raw_output.get("warnings") or [])
        status = self._result_status(field_count, requires_review_count, error_count, warning_count)

        result = self.repository.create_result(
            job=job,
            status=status.value,
            field_count=field_count,
            normalized_count=normalized_count,
            requires_review_count=requires_review_count,
            error_count=error_count,
            warning_count=warning_count,
        )

        for raw_object in object_specs:
            self.repository.add_object(
                result=result,
                field_path=str(raw_object.get("field_path") or ""),
                field_type=str(raw_object.get("field_type") or "object"),
                object_type=str(raw_object.get("field_type") or "object"),
                status=ExtractedFieldStatus.NORMALIZED.value,
            )

        for array_item in array_items:
            statuses = [
                preview["status"]
                for preview in normalized_previews
                if preview["item_index"] == array_item["item_index"] and preview["field_path"].startswith(str(array_item["array_field_path"]).replace("[]", "[]"))
            ]
            item_status = ExtractedFieldStatus.REQUIRES_REVIEW.value if any(status in REVIEW_STATUSES for status in statuses) else ExtractedFieldStatus.NORMALIZED.value
            item_confidence = min(
                [preview["confidence"] for preview in normalized_previews if preview["item_index"] == array_item["item_index"]] or [0.0]
            )
            self.repository.add_array_item(
                result=result,
                array_field_path=str(array_item["array_field_path"]),
                item_index=array_item["item_index"],
                status=item_status,
                confidence=item_confidence,
            )

        for preview in normalized_previews:
            field_value = self.repository.add_field_value(
                result=result,
                field_id=preview["field_id"],
                field_path=preview["field_path"],
                field_type=preview["field_type"],
                raw_value=preview["raw_value"],
                normalized_value=preview["normalized_value"],
                display_value=preview["display_value"],
                normalized_json=preview["normalized_json"],
                metadata_json=preview["metadata_json"],
                confidence=preview["confidence"],
                status=preview["status"],
                is_required=preview["is_required"],
                item_index=preview["item_index"],
            )
            if preview["evidence"]:
                self.repository.add_evidence(
                    result=result,
                    field_value_id=field_value.id,
                    document_id=job.document_id,
                    evidence=preview["evidence"],
                    template_id=job.template_id,
                    template_version_id=job.template_version_id,
                )

        run.status = NormalizationRunStatus.COMPLETED.value
        run.extraction_result_id = result.id
        run.finished_at = datetime.now(UTC)
        self.session.flush()
        return ResultProcessingOutcome(result=result, status=status)

    def _normalize_raw_field(self, raw_field: dict[str, Any], field_definitions: dict[str, dict[str, Any]], *, item_index: int | None) -> dict[str, Any]:
        field_path = str(raw_field.get("field_path") or raw_field.get("fieldPath") or "")
        definition = field_definitions.get(field_path, {})
        field_type = str(
            raw_field.get("data_type")
            or raw_field.get("field_type")
            or definition.get("dataType")
            or definition.get("fieldType")
            or definition.get("type")
            or "text"
        ).lower()
        raw_status = str(raw_field.get("status") or "extracted")
        raw_value = raw_field.get("raw_value")
        normalized = self.normalizer.normalize(raw_value, field_type)
        evidence = raw_field.get("evidence")
        evidence_exists = bool(evidence)
        worker_confidence = float(raw_field.get("confidence") or 0.0)
        final_confidence = self.confidence.final_confidence(
            worker_confidence=worker_confidence,
            normalization_success=normalized.success,
            evidence_exists=evidence_exists,
            raw_status=raw_status,
        )
        is_required = bool(definition.get("isRequired") or definition.get("required") or definition.get("is_required"))
        important = bool(definition.get("important") or definition.get("isImportant") or definition.get("is_important"))
        status = self.confidence.status(
            raw_status=raw_status,
            normalization_success=normalized.success,
            evidence_exists=evidence_exists,
            confidence=final_confidence,
            is_required=is_required,
        ).value
        return {
            "field_id": raw_field.get("field_id") or raw_field.get("fieldId") or definition.get("id"),
            "field_path": field_path,
            "field_type": field_type,
            "raw_value": raw_value,
            "normalized_value": None if normalized.normalized_value is None else str(normalized.normalized_value),
            "display_value": normalized.display_value,
            "normalized_json": {"value": normalized.normalized_value, "success": normalized.success, "error_code": normalized.error_code},
            "metadata_json": normalized.metadata | {"important": important, "label": definition.get("label")},
            "confidence": final_confidence,
            "status": status,
            "is_required": is_required,
            "item_index": item_index,
            "evidence": evidence,
        }

    def _field_definitions(self, fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        definitions = {}
        for field in fields:
            path = field.get("fieldPath") or field.get("field_path") or field.get("path")
            if path:
                definitions[str(path)] = field
        return definitions

    def _array_child_path(self, array_path: str, key: str, field_definitions: dict[str, dict[str, Any]]) -> str:
        candidate = f"{array_path}.{key}"
        if candidate in field_definitions:
            return candidate
        normalized_parent = str(array_path).replace("[]", "")
        for path in field_definitions:
            if path.replace("[]", "").endswith(f"{normalized_parent}.{key}"):
                return path
        return candidate

    def _result_status(
        self,
        field_count: int,
        requires_review_count: int,
        error_count: int,
        warning_count: int,
    ) -> ExtractionResultStatus:
        if error_count and field_count == 0:
            return ExtractionResultStatus.FAILED
        if requires_review_count:
            return ExtractionResultStatus.REQUIRES_REVIEW
        if warning_count or error_count:
            return ExtractionResultStatus.COMPLETED_WITH_WARNINGS
        return ExtractionResultStatus.COMPLETED

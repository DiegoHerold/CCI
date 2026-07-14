import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PACKAGE = Path(__file__).resolve().parents[1]


def validate(schema_name: str, example_name: str) -> None:
    schema = json.loads((PACKAGE / schema_name).read_text(encoding="utf-8"))
    example = json.loads((PACKAGE / "examples" / example_name).read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)


def test_document_example_matches_schema() -> None:
    validate("document.schema.json", "document.example.json")


def test_evidence_example_matches_schema() -> None:
    validate("evidence.schema.json", "evidence.example.json")


def test_preview_schema_is_valid() -> None:
    schema = json.loads((PACKAGE / "preview.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_upload_schema_is_valid() -> None:
    schema = json.loads((PACKAGE / "upload.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


def test_selection_schema_is_valid() -> None:
    schema = json.loads((PACKAGE / "selection.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

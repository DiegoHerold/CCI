import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource


PACKAGE = Path(__file__).resolve().parents[1]
SCHEMAS = PACKAGE / "schemas"


EVENT_CASES = [
    ("file-imported.schema.json", "file-imported.example.json"),
    ("document-classified.schema.json", "document-classified.example.json"),
    ("document-confirmed.schema.json", "document-confirmed.example.json"),
    ("raw-extracted.schema.json", "raw-extracted.example.json"),
    ("variables-ready.schema.json", "variables-ready.example.json"),
    ("execution-started.schema.json", "execution-started.example.json"),
    ("rule-executed.schema.json", "rule-executed.example.json"),
    ("result-created.schema.json", "result-created.example.json"),
    ("execution-finished.schema.json", "execution-finished.example.json"),
    ("report-generated.schema.json", "report-generated.example.json"),
    ("log-created.schema.json", "log-created.example.json"),
    ("template-version-published.schema.json", "template-version-published.example.json"),
    ("template-manually-confirmed.schema.json", "template-manually-confirmed.example.json"),
]


@pytest.mark.parametrize(("schema_name", "example_name"), EVENT_CASES)
def test_event_example_matches_schema(schema_name: str, example_name: str) -> None:
    envelope = json.loads((SCHEMAS / "event-envelope.schema.json").read_text(encoding="utf-8"))
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    example = json.loads((PACKAGE / "examples" / example_name).read_text(encoding="utf-8"))
    registry = Registry().with_resource(envelope["$id"], Resource.from_contents(envelope))

    Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(example)

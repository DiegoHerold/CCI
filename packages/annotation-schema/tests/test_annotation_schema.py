import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_annotation_schema_is_valid() -> None:
    path = Path(__file__).resolve().parents[1] / "annotation.schema.json"
    Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PACKAGE = Path(__file__).resolve().parents[1]


def test_variable_example_matches_schema() -> None:
    schema = json.loads((PACKAGE / "variable.schema.json").read_text(encoding="utf-8"))
    example = json.loads((PACKAGE / "examples" / "variable.example.json").read_text(encoding="utf-8"))

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)

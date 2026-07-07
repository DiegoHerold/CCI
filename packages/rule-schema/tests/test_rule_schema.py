import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker


PACKAGE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "example_name",
    ["rule.equals.example.json", "rule.exists.example.json", "rule.sum_equals.example.json"],
)
def test_rule_examples_match_schema(example_name: str) -> None:
    schema = json.loads((PACKAGE / "rule.schema.json").read_text(encoding="utf-8"))
    example = json.loads((PACKAGE / "examples" / example_name).read_text(encoding="utf-8"))

    Draft202012Validator(schema, format_checker=FormatChecker()).validate(example)

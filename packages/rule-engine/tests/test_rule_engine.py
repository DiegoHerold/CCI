import sys
from pathlib import Path

import pytest


PYTHON_DIR = Path(__file__).resolve().parents[1] / "python"
sys.path.insert(0, str(PYTHON_DIR))

from engine import evaluate_rule  # noqa: E402
from models import ResultStatus  # noqa: E402


def rule(operator: str, **logic) -> dict:
    return {"logic": {"operator": operator, **logic}, "required_variables": []}


def test_equals_approved() -> None:
    result = evaluate_rule(rule("equals", left="a", right="b"), {"a": 10, "b": 10})
    assert result.status == ResultStatus.APPROVED


def test_equals_divergent() -> None:
    result = evaluate_rule(rule("equals", left="a", right="b"), {"a": 10, "b": 11})
    assert result.status == ResultStatus.DIVERGENT


def test_equals_with_tolerance() -> None:
    result = evaluate_rule(rule("equals", left="a", right="b", tolerance=0.01), {"a": 10, "b": 10.009})
    assert result.status == ResultStatus.APPROVED


@pytest.mark.parametrize(
    ("operator", "left", "right"),
    [
        ("not_equals", 10, 11),
        ("greater_than", 11, 10),
        ("less_than", 9, 10),
        ("greater_or_equal", 10, 10),
        ("less_or_equal", 10, 10),
        ("difference_less_than", 10, 10.005),
    ],
)
def test_comparison_operators(operator: str, left: float, right: float) -> None:
    result = evaluate_rule(
        rule(operator, left="a", right="b", tolerance=0.01),
        {"a": left, "b": right},
    )
    assert result.status == ResultStatus.APPROVED


def test_exists_approved() -> None:
    result = evaluate_rule(rule("exists", left="a"), {"a": 10})
    assert result.status == ResultStatus.APPROVED


def test_not_exists_approved() -> None:
    result = evaluate_rule(rule("not_exists", left="a"), {})
    assert result.status == ResultStatus.APPROVED


def test_sum_equals_approved() -> None:
    result = evaluate_rule(
        rule("sum_equals", items=["a", "b"], right="total", tolerance=0.01),
        {"a": 10, "b": 20, "total": 30},
    )
    assert result.status == ResultStatus.APPROVED


def test_missing_required_variable_returns_pending() -> None:
    candidate = rule("equals", left="a", right="b")
    candidate["required_variables"] = ["a", "b"]
    result = evaluate_rule(candidate, {"a": 10})
    assert result.status == ResultStatus.PENDING


def test_unknown_operator_returns_error() -> None:
    result = evaluate_rule(rule("execute_python", left="a"), {"a": 10})
    assert result.status == ResultStatus.ERROR


def test_and_approved() -> None:
    result = evaluate_rule(
        rule(
            "and",
            conditions=[
                {"operator": "equals", "left": "a", "right": "b"},
                {"operator": "greater_than", "left": "c", "right": "d"},
            ],
        ),
        {"a": 10, "b": 10, "c": 2, "d": 1},
    )
    assert result.status == ResultStatus.APPROVED


def test_or_approved() -> None:
    result = evaluate_rule(
        rule(
            "or",
            conditions=[
                {"operator": "equals", "left": "a", "right": "b"},
                {"operator": "greater_than", "left": "c", "right": "d"},
            ],
        ),
        {"a": 10, "b": 11, "c": 2, "d": 1},
    )
    assert result.status == ResultStatus.APPROVED

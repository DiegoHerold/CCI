from numbers import Real
from typing import Any, Iterable


def is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)


def numeric_difference(left: Any, right: Any) -> float | None:
    if not is_number(left) or not is_number(right):
        return None
    return abs(float(left) - float(right))


def equals(left: Any, right: Any, tolerance: float = 0.0) -> tuple[bool, float | None]:
    difference = numeric_difference(left, right)
    if difference is not None:
        return difference <= tolerance, difference
    return left == right, None


def not_equals(left: Any, right: Any, tolerance: float = 0.0) -> tuple[bool, float | None]:
    matched, difference = equals(left, right, tolerance)
    return not matched, difference


def compare_order(operator: str, left: Any, right: Any) -> bool:
    if operator == "greater_than":
        return left > right
    if operator == "less_than":
        return left < right
    if operator == "greater_or_equal":
        return left >= right
    if operator == "less_or_equal":
        return left <= right
    raise ValueError(f"Unsupported order operator: {operator}")


def difference_less_than(left: Any, right: Any, limit: float) -> tuple[bool, float]:
    difference = numeric_difference(left, right)
    if difference is None:
        raise TypeError("difference_less_than requires numeric operands")
    return difference < limit, difference


def sum_values(values: Iterable[Any]) -> float:
    materialized = list(values)
    if not all(is_number(value) for value in materialized):
        raise TypeError("sum_equals requires numeric variables")
    return sum(float(value) for value in materialized)

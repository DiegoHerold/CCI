from collections.abc import Mapping
from typing import Any

from models import ResultStatus, RuleEvaluationResult
from operators import (
    compare_order,
    difference_less_than,
    equals,
    not_equals,
    numeric_difference,
    sum_values,
)


SUPPORTED_OPERATORS = frozenset(
    {
        "equals",
        "not_equals",
        "greater_than",
        "less_than",
        "greater_or_equal",
        "less_or_equal",
        "exists",
        "not_exists",
        "difference_less_than",
        "sum_equals",
        "and",
        "or",
    }
)


def _result(
    status: ResultStatus,
    operator: str,
    message: str,
    *,
    left_value: Any | None = None,
    right_value: Any | None = None,
    difference: float | None = None,
    details: list[RuleEvaluationResult] | None = None,
) -> RuleEvaluationResult:
    return RuleEvaluationResult(
        status=status,
        operator=operator,
        left_value=left_value,
        right_value=right_value,
        difference=difference,
        message=message,
        details=details or [],
    )


def _resolve(operand: Any, variables: Mapping[str, Any]) -> tuple[bool, Any]:
    if isinstance(operand, str):
        return operand in variables, variables.get(operand)
    return True, operand


def _pending(operator: str, missing: list[str]) -> RuleEvaluationResult:
    return _result(
        ResultStatus.PENDING,
        operator,
        f"Variáveis obrigatórias ausentes: {', '.join(sorted(missing))}.",
    )


def _evaluate_boolean_group(
    operator: str,
    conditions: Any,
    variables: Mapping[str, Any],
) -> RuleEvaluationResult:
    if not isinstance(conditions, list) or not conditions:
        return _result(
            ResultStatus.ERROR,
            operator,
            "O operador lógico requer uma lista não vazia de condições.",
        )

    details = [_evaluate_logic(condition, variables) for condition in conditions]
    statuses = [detail.status for detail in details]

    if operator == "and":
        if ResultStatus.ERROR in statuses:
            status = ResultStatus.ERROR
        elif ResultStatus.PENDING in statuses:
            status = ResultStatus.PENDING
        elif all(status == ResultStatus.APPROVED for status in statuses):
            status = ResultStatus.APPROVED
        else:
            status = ResultStatus.DIVERGENT
    else:
        if ResultStatus.APPROVED in statuses:
            status = ResultStatus.APPROVED
        elif ResultStatus.PENDING in statuses:
            status = ResultStatus.PENDING
        elif ResultStatus.ERROR in statuses:
            status = ResultStatus.ERROR
        else:
            status = ResultStatus.DIVERGENT

    messages = {
        ResultStatus.APPROVED: "Condição lógica aprovada.",
        ResultStatus.DIVERGENT: "Condição lógica divergente.",
        ResultStatus.PENDING: "Condição lógica pendente por variável ausente.",
        ResultStatus.ERROR: "Erro ao avaliar condição lógica.",
    }
    return _result(status, operator, messages[status], details=details)


def _evaluate_logic(logic: Mapping[str, Any], variables: Mapping[str, Any]) -> RuleEvaluationResult:
    operator = str(logic.get("operator", ""))
    if operator not in SUPPORTED_OPERATORS:
        return _result(
            ResultStatus.ERROR,
            operator or "unknown",
            f"Operador não suportado: {operator or 'ausente'}.",
        )

    if operator in {"and", "or"}:
        return _evaluate_boolean_group(operator, logic.get("conditions"), variables)

    left_operand = logic.get("left")
    if operator in {"exists", "not_exists"}:
        if not isinstance(left_operand, str):
            return _result(ResultStatus.ERROR, operator, "O operador exige uma chave de variável em left.")
        present = left_operand in variables and variables[left_operand] is not None
        passed = present if operator == "exists" else not present
        return _result(
            ResultStatus.APPROVED if passed else ResultStatus.DIVERGENT,
            operator,
            "Condição de existência atendida." if passed else "Condição de existência não atendida.",
            left_value=variables.get(left_operand),
        )

    if operator == "sum_equals":
        items = logic.get("items")
        if not isinstance(items, list) or not items or not all(isinstance(item, str) for item in items):
            return _result(ResultStatus.ERROR, operator, "sum_equals exige uma lista de chaves em items.")
        missing = [item for item in items if item not in variables]
        right_found, right_value = _resolve(logic.get("right"), variables)
        if not right_found and isinstance(logic.get("right"), str):
            missing.append(logic["right"])
        if missing:
            return _pending(operator, missing)
        try:
            left_value = sum_values(variables[item] for item in items)
            tolerance = float(logic.get("tolerance", 0.0))
            passed, difference = equals(left_value, right_value, tolerance)
        except (TypeError, ValueError) as exc:
            return _result(ResultStatus.ERROR, operator, str(exc))
        return _result(
            ResultStatus.APPROVED if passed else ResultStatus.DIVERGENT,
            operator,
            "Soma confere dentro da tolerância." if passed else "Soma divergente.",
            left_value=left_value,
            right_value=right_value,
            difference=difference,
        )

    left_found, left_value = _resolve(left_operand, variables)
    right_operand = logic.get("right")
    right_found, right_value = _resolve(right_operand, variables)
    missing = []
    if not left_found and isinstance(left_operand, str):
        missing.append(left_operand)
    if not right_found and isinstance(right_operand, str):
        missing.append(right_operand)
    if missing:
        return _pending(operator, missing)

    try:
        tolerance = float(logic.get("tolerance", 0.0))
        difference = numeric_difference(left_value, right_value)
        if operator == "equals":
            passed, difference = equals(left_value, right_value, tolerance)
        elif operator == "not_equals":
            passed, difference = not_equals(left_value, right_value, tolerance)
        elif operator in {"greater_than", "less_than", "greater_or_equal", "less_or_equal"}:
            passed = compare_order(operator, left_value, right_value)
        elif operator == "difference_less_than":
            if "tolerance" not in logic:
                return _result(ResultStatus.ERROR, operator, "difference_less_than exige tolerance.")
            passed, difference = difference_less_than(left_value, right_value, tolerance)
        else:
            return _result(ResultStatus.ERROR, operator, "Operador sem implementação.")
    except (TypeError, ValueError) as exc:
        return _result(ResultStatus.ERROR, operator, str(exc))

    return _result(
        ResultStatus.APPROVED if passed else ResultStatus.DIVERGENT,
        operator,
        "Valores conferem dentro da tolerância." if passed else "Valores divergem.",
        left_value=left_value,
        right_value=right_value,
        difference=difference,
    )


def evaluate_rule(
    rule: Mapping[str, Any],
    variables: Mapping[str, Any],
) -> RuleEvaluationResult:
    logic = rule.get("logic")
    operator = str(logic.get("operator", "unknown")) if isinstance(logic, Mapping) else "unknown"
    if not isinstance(logic, Mapping):
        return _result(ResultStatus.ERROR, operator, "Regra sem objeto logic válido.")

    required = rule.get("required_variables", [])
    if not isinstance(required, list):
        return _result(ResultStatus.ERROR, operator, "required_variables deve ser uma lista.")
    missing = [key for key in required if isinstance(key, str) and key not in variables]
    if missing:
        return _pending(operator, missing)

    return _evaluate_logic(logic, variables)

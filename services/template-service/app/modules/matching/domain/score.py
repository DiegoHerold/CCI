from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from app.infrastructure.database.models import IdentificationSignal
from app.modules.matching.domain.document_profile import normalize_text


@dataclass
class ScoreResult:
    score: float
    eliminated: bool = False
    matched_signals: list[str] = field(default_factory=list)
    missing_required_signals: list[str] = field(default_factory=list)
    negative_matches: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def _values(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, list):
        return [str(item) for item in parsed if str(item).strip()]
    if isinstance(parsed, dict):
        return [str(item) for item in parsed.values() if str(item).strip()]
    return [item.strip() for item in re.split(r"[,|;]", value) if item.strip()]


def _bool_value(value: str) -> bool:
    return normalize_text(value) not in {"", "0", "false", "nao", "não", "no"}


def _page_range(value: str) -> tuple[int | None, int | None]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        minimum = parsed.get("min")
        maximum = parsed.get("max")
        return (int(minimum) if minimum is not None else None, int(maximum) if maximum is not None else None)
    match = re.match(r"^\s*(\d*)\s*-\s*(\d*)\s*$", value)
    if match:
        low, high = match.groups()
        return (int(low) if low else None, int(high) if high else None)
    try:
        number = int(value)
    except ValueError:
        return -1, -1
    return number, number


def _signal_found(signal: IdentificationSignal, profile: dict[str, Any]) -> bool:
    kind = signal.signal_type
    text = profile.get("normalized_text_sample", "")
    raw_value = signal.value
    normalized_value = normalize_text(raw_value)

    if kind == "contains_text":
        return normalized_value in text
    if kind == "contains_any_text":
        return any(normalize_text(item) in text for item in _values(raw_value))
    if kind == "contains_all_text":
        return all(normalize_text(item) in text for item in _values(raw_value))
    if kind == "not_contains_text":
        return normalized_value not in text
    if kind == "regex":
        try:
            return re.search(raw_value, profile.get("text_sample", "")[:10000]) is not None
        except re.error:
            return False
    if kind == "file_format":
        return normalize_text(profile.get("file_format")) == normalize_text(raw_value)
    if kind == "sheet_name":
        names = [normalize_text(item) for item in profile.get("sheet_names", [])]
        return normalized_value in names
    if kind in {"column_header", "table_header"}:
        headers = [normalize_text(item) for item in profile.get("detected_headers", [])]
        return normalized_value in headers or normalized_value in text
    if kind == "page_count_range":
        minimum, maximum = _page_range(raw_value)
        page_count = int(profile.get("page_count") or 0)
        return (minimum is None or page_count >= minimum) and (maximum is None or page_count <= maximum)
    if kind == "has_cnpj":
        return bool(profile.get("has_cnpj")) == _bool_value(raw_value)
    if kind == "has_date":
        return bool(profile.get("has_dates")) == _bool_value(raw_value)
    if kind == "has_currency_values":
        return bool(profile.get("has_currency_values")) == _bool_value(raw_value)
    if kind == "structure_hint":
        hints = [normalize_text(item) for item in profile.get("structure_hints", [])]
        return normalized_value in hints
    return False


def score_signals(signals: list[IdentificationSignal], profile: dict[str, Any]) -> ScoreResult:
    result = ScoreResult(score=0.0, details={"signals": []})
    if not signals:
        result.details["reason"] = "template_without_identification_signals"
        return result

    total_weight = sum(max(signal.weight, 0.0) for signal in signals if not signal.negative) or 1.0
    positive = 0.0
    penalty = 0.0

    for signal in signals:
        label = f"{signal.signal_type}:{signal.value}"
        found = _signal_found(signal, profile)
        detail = {
            "signal_id": signal.id,
            "signal_type": signal.signal_type,
            "value": signal.value,
            "weight": signal.weight,
            "required": signal.required,
            "negative": signal.negative,
            "found": found,
        }
        result.details["signals"].append(detail)

        if signal.signal_type == "not_contains_text" and signal.negative:
            # For negative not_contains_text, a missing prohibition is good; present text penalizes.
            found = not found
            detail["found"] = found

        if signal.negative:
            if found:
                penalty += max(signal.weight, 0.0)
                result.negative_matches.append(label)
                if signal.required:
                    result.missing_required_signals.append(label)
                    result.eliminated = True
            continue

        if found:
            positive += max(signal.weight, 0.0)
            result.matched_signals.append(label)
        elif signal.required:
            result.missing_required_signals.append(label)
            result.eliminated = True

    if result.eliminated:
        result.score = 0.0
    else:
        result.score = max(0.0, min(1.0, (positive - penalty) / total_weight))
    result.details["positive_weight"] = positive
    result.details["negative_penalty"] = penalty
    result.details["total_positive_weight"] = total_weight
    return result

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


MONTHS = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
}


@dataclass(frozen=True)
class NormalizedValue:
    raw_value: Any
    normalized_value: Any = None
    display_value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_code: str | None = None
    error_message: str | None = None


class ValueNormalizer:
    def normalize(self, raw_value: Any, field_type: str | None) -> NormalizedValue:
        normalized_type = (field_type or "text").lower()
        if raw_value is None or raw_value == "":
            return NormalizedValue(raw_value=raw_value, success=False, error_code="empty_value", error_message="value is empty")
        if normalized_type in {"text", "string"}:
            return self.text(raw_value)
        if normalized_type in {"number", "integer", "decimal"}:
            return self.number(raw_value)
        if normalized_type in {"money", "currency"}:
            return self.money(raw_value)
        if normalized_type == "date":
            return self.date(raw_value)
        if normalized_type in {"month", "competence"}:
            return self.month(raw_value)
        if normalized_type == "cnpj":
            return self.cnpj(raw_value)
        if normalized_type == "cpf":
            return self.cpf(raw_value)
        if normalized_type == "boolean":
            return self.boolean(raw_value)
        if normalized_type in {"percentage", "percent"}:
            return self.percentage(raw_value)
        if normalized_type in {"account_code", "account"}:
            return self.account_code(raw_value)
        return self.text(raw_value)

    def text(self, raw_value: Any) -> NormalizedValue:
        display = re.sub(r"\s+", " ", str(raw_value).replace("\r", "\n")).strip()
        return NormalizedValue(raw_value=raw_value, normalized_value=display, display_value=display)

    def number(self, raw_value: Any) -> NormalizedValue:
        parsed = _parse_decimal(raw_value)
        if parsed is None:
            return _failed(raw_value, "invalid_number")
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=str(parsed),
            display_value=_format_decimal_pt_br(parsed),
            metadata={"decimal": str(parsed)},
        )

    def money(self, raw_value: Any) -> NormalizedValue:
        text = str(raw_value).strip()
        dc_match = re.search(r"\b([DC])\b$", text, flags=re.IGNORECASE)
        dc_indicator = dc_match.group(1).upper() if dc_match else None
        parsed = _parse_decimal(text)
        if parsed is None:
            return _failed(raw_value, "invalid_money")
        metadata: dict[str, Any] = {"decimal": str(parsed)}
        if dc_indicator:
            metadata["dc_indicator"] = dc_indicator
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=str(parsed),
            display_value=f"R$ {_format_decimal_pt_br(parsed)}",
            metadata=metadata,
        )

    def date(self, raw_value: Any) -> NormalizedValue:
        parsed = _parse_date(str(raw_value).strip())
        if parsed is None:
            return _failed(raw_value, "invalid_date")
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=parsed.isoformat(),
            display_value=parsed.strftime("%d/%m/%Y"),
        )

    def month(self, raw_value: Any) -> NormalizedValue:
        parsed = _parse_month(str(raw_value).strip())
        if parsed is None:
            return _failed(raw_value, "invalid_month")
        year, month = parsed
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=f"{year:04d}-{month:02d}",
            display_value=f"{month:02d}/{year:04d}",
            metadata={"year": year, "month": month},
        )

    def cnpj(self, raw_value: Any) -> NormalizedValue:
        digits = _digits(raw_value)
        if len(digits) != 14:
            return _failed(raw_value, "invalid_cnpj_length")
        is_valid = _validate_cnpj(digits)
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=digits,
            display_value=f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}",
            metadata={"is_valid": is_valid},
            success=is_valid,
            error_code=None if is_valid else "invalid_cnpj_check_digit",
            error_message=None if is_valid else "invalid CNPJ check digit",
        )

    def cpf(self, raw_value: Any) -> NormalizedValue:
        digits = _digits(raw_value)
        if len(digits) != 11:
            return _failed(raw_value, "invalid_cpf_length")
        is_valid = _validate_cpf(digits)
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=digits,
            display_value=f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}",
            metadata={"is_valid": is_valid},
            success=is_valid,
            error_code=None if is_valid else "invalid_cpf_check_digit",
            error_message=None if is_valid else "invalid CPF check digit",
        )

    def boolean(self, raw_value: Any) -> NormalizedValue:
        text = str(raw_value).strip().casefold()
        true_values = {"sim", "s", "true", "1", "ativo", "ok", "yes", "y"}
        false_values = {"nao", "não", "n", "false", "0", "inativo", "erro", "no"}
        if text in true_values:
            return NormalizedValue(raw_value=raw_value, normalized_value=True, display_value="Sim")
        if text in false_values:
            return NormalizedValue(raw_value=raw_value, normalized_value=False, display_value="Nao")
        return _failed(raw_value, "invalid_boolean")

    def percentage(self, raw_value: Any) -> NormalizedValue:
        text = str(raw_value).strip()
        has_percent = "%" in text
        parsed = _parse_decimal(text.replace("%", ""))
        if parsed is None:
            return _failed(raw_value, "invalid_percentage")
        normalized = parsed / Decimal("100") if has_percent else parsed
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=str(normalized),
            display_value=f"{_format_decimal_pt_br(parsed)}%" if has_percent else str(normalized),
            metadata={"decimal": str(normalized)},
        )

    def account_code(self, raw_value: Any) -> NormalizedValue:
        text = re.sub(r"\s+", "", str(raw_value).strip())
        if not re.match(r"^\d+(?:\.\d+)*$", text):
            return _failed(raw_value, "invalid_account_code")
        level = text.count(".") + 1
        return NormalizedValue(
            raw_value=raw_value,
            normalized_value=text,
            display_value=text,
            metadata={"level": level},
        )


def _failed(raw_value: Any, code: str) -> NormalizedValue:
    return NormalizedValue(raw_value=raw_value, success=False, error_code=code, error_message=code)


def _digits(value: Any) -> str:
    return re.sub(r"\D", "", str(value))


def _parse_decimal(value: Any) -> Decimal | None:
    if isinstance(value, int | float | Decimal):
        return Decimal(str(value))
    text = str(value).strip().upper()
    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = re.sub(r"\b[DC]\b$", "", text)
    text = text.replace("R$", "").replace("%", "").replace("(", "").replace(")", "").replace("+", "").replace("-", "")
    text = re.sub(r"[^0-9,\.]", "", text)
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        parsed = Decimal(text)
    except InvalidOperation:
        return None
    return -parsed if negative else parsed


def _format_decimal_pt_br(value: Decimal) -> str:
    sign = "-" if value < 0 else ""
    quantized = abs(value).quantize(Decimal("0.01"))
    whole, _, cents = f"{quantized:.2f}".partition(".")
    groups = []
    while whole:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    return f"{sign}{'.'.join(groups)},{cents}"


def _parse_date(value: str) -> date | None:
    match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", value)
    if match:
        day, month, year = [int(part) for part in match.groups()]
        return _safe_date(year, month, day)
    match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", value)
    if match:
        year, month, day = [int(part) for part in match.groups()]
        return _safe_date(year, month, day)
    parsed_month = _parse_month(value)
    if parsed_month:
        year, month = parsed_month
        return date(year, month, 1)
    return None


def _parse_month(value: str) -> tuple[int, int] | None:
    normalized = _strip_accents(value).casefold()
    match = re.match(r"^(\d{1,2})/(\d{4})$", normalized)
    if match:
        month, year = [int(part) for part in match.groups()]
        return (year, month) if 1 <= month <= 12 else None
    match = re.match(r"^(\d{4})-(\d{1,2})$", normalized)
    if match:
        year, month = [int(part) for part in match.groups()]
        return (year, month) if 1 <= month <= 12 else None
    match = re.match(r"^([a-z]+)[/-](\d{4})$", normalized)
    if match:
        month_name, year = match.groups()
        month = MONTHS.get(month_name)
        return (int(year), month) if month else None
    return None


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _strip_accents(value: str) -> str:
    replacements = str.maketrans({"ç": "c", "Ç": "C", "ã": "a", "õ": "o", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "â": "a", "ê": "e", "ô": "o"})
    return value.translate(replacements)


def _validate_cnpj(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    weights_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights_2 = [6, *weights_1]
    return digits[-2:] == f"{_check_digit(digits[:12], weights_1)}{_check_digit(digits[:13], weights_2)}"


def _validate_cpf(digits: str) -> bool:
    if len(set(digits)) == 1:
        return False
    first = _check_digit(digits[:9], list(range(10, 1, -1)))
    second = _check_digit(digits[:10], list(range(11, 1, -1)))
    return digits[-2:] == f"{first}{second}"


def _check_digit(base: str, weights: list[int]) -> int:
    total = sum(int(digit) * weight for digit, weight in zip(base, weights, strict=False))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder

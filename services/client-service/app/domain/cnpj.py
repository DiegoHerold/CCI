import re


def normalize_cnpj(value: str) -> str:
    return re.sub(r"\D", "", value)


def is_valid_cnpj(value: str) -> bool:
    digits = normalize_cnpj(value)
    if len(digits) != 14 or len(set(digits)) == 1:
        return False

    def check_digit(base: str, weights: list[int]) -> str:
        total = sum(int(digit) * weight for digit, weight in zip(base, weights))
        remainder = total % 11
        return "0" if remainder < 2 else str(11 - remainder)

    first = check_digit(digits[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second = check_digit(
        digits[:12] + first, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    )
    return digits[-2:] == first + second


def format_cnpj(value: str) -> str:
    digits = normalize_cnpj(value)
    if len(digits) != 14:
        return value
    return (
        f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/"
        f"{digits[8:12]}-{digits[12:]}"
    )


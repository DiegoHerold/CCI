import pytest

from app.domain.cnpj import format_cnpj, is_valid_cnpj, normalize_cnpj
from app.domain.folders import resolve_competence_path, validate_folder_pattern


@pytest.mark.parametrize(
    "value",
    ["12.345.678/0001-95", "12345678000195"],
)
def test_valid_cnpj(value: str) -> None:
    assert is_valid_cnpj(value)
    assert normalize_cnpj(value) == "12345678000195"
    assert format_cnpj(value) == "12.345.678/0001-95"


@pytest.mark.parametrize(
    "value",
    ["00.000.000/0000-00", "11.111.111/1111-11", "123", "abc", "12.345.678/0001-00"],
)
def test_invalid_cnpj(value: str) -> None:
    assert not is_valid_cnpj(value)


def test_folder_resolution_supports_windows_and_previous_month() -> None:
    assert resolve_competence_path(
        "R:\\Clientes\\Empresa", "{{YYYY}}/{{MM}}", 2026, 7
    ) == "R:\\Clientes\\Empresa\\2026\\07"
    assert resolve_competence_path(
        "/mnt/client", "{{previousMonth.YYYY}}/{{previousMonth.MM}}", 2026, 1
    ) == "/mnt/client/2025/12"


def test_folder_pattern_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        validate_folder_pattern("../{{YYYY}}")


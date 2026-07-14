from app.modules.normalization.normalizers import ValueNormalizer


def test_normalizes_cnpj_formatted_and_unformatted() -> None:
    normalizer = ValueNormalizer()

    formatted = normalizer.cnpj("11.222.333/0001-81")
    unformatted = normalizer.cnpj("11222333000181")

    assert formatted.normalized_value == "11222333000181"
    assert unformatted.display_value == "11.222.333/0001-81"
    assert formatted.success is True


def test_marks_invalid_cnpj() -> None:
    result = ValueNormalizer().cnpj("00.000.000/0001-00")

    assert result.success is False
    assert result.error_code == "invalid_cnpj_check_digit"


def test_normalizes_brazilian_money_and_signs() -> None:
    normalizer = ValueNormalizer()

    assert normalizer.money("R$ 1.234,56").normalized_value == "1234.56"
    assert normalizer.money("-1.234,56").normalized_value == "-1234.56"
    assert normalizer.money("(1.234,56)").normalized_value == "-1234.56"
    with_indicator = normalizer.money("1.234,56 C")
    assert with_indicator.metadata["dc_indicator"] == "C"


def test_normalizes_date_month_number_percentage_and_account_code() -> None:
    normalizer = ValueNormalizer()

    assert normalizer.date("01/07/2026").normalized_value == "2026-07-01"
    assert normalizer.month("07/2026").normalized_value == "2026-07"
    assert normalizer.number("1.234,56").normalized_value == "1234.56"
    assert normalizer.percentage("10,5%").normalized_value == "0.105"
    account = normalizer.account_code("1.1.01")
    assert account.normalized_value == "1.1.01"
    assert account.metadata["level"] == 3


def test_handles_empty_and_invalid_values_without_exception() -> None:
    normalizer = ValueNormalizer()

    assert normalizer.normalize("", "text").success is False
    assert normalizer.money("abc").error_code == "invalid_money"

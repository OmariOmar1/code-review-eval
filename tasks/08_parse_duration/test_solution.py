import pytest

from solution import parse_duration


def test_seconds_only():
    assert parse_duration("45s") == 45


def test_combined_units():
    assert parse_duration("1h30m") == 5400


def test_all_units():
    assert parse_duration("1d2h3m4s") == 93784


def test_spaces_and_case():
    assert parse_duration("  2H 15M ") == 8100


def test_multi_digit_and_zero():
    assert parse_duration("120m") == 7200
    assert parse_duration("0s") == 0


@pytest.mark.parametrize("bad", ["", "   ", "abc", "10", "5x", "1h30", "h", "1.5h", "-5m"])
def test_invalid_input_raises(bad):
    with pytest.raises(ValueError):
        parse_duration(bad)

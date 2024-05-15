import pytest

from solution import roman_to_int


@pytest.mark.parametrize(
    "numeral, expected",
    [
        ("I", 1),
        ("III", 3),
        ("IV", 4),
        ("IX", 9),
        ("XL", 40),
        ("XC", 90),
        ("CD", 400),
        ("CM", 900),
        ("LVIII", 58),
        ("MCMXCIV", 1994),
        ("MMXXIV", 2024),
        ("MMMCMXCIX", 3999),
    ],
)
def test_roman_to_int(numeral, expected):
    assert roman_to_int(numeral) == expected

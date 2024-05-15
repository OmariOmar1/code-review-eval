from solution import is_palindrome


def test_simple_word():
    assert is_palindrome("racecar") is True


def test_not_palindrome():
    assert is_palindrome("python") is False


def test_mixed_case():
    assert is_palindrome("RaceCar") is True


def test_ignores_punctuation_and_spaces():
    assert is_palindrome("A man, a plan, a canal: Panama") is True


def test_punctuation_non_palindrome():
    assert is_palindrome("race a car") is False


def test_empty_string():
    assert is_palindrome("") is True


def test_only_punctuation():
    assert is_palindrome(".,!") is True


def test_digits():
    assert is_palindrome("12 3 21") is True
    assert is_palindrome("1231") is False

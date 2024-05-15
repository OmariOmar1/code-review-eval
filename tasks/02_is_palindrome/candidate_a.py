"""Palindrome helper."""


def is_palindrome(text):
    """Return True if ``text`` is a palindrome, ignoring letter case.

    >>> is_palindrome("racecar")
    True
    >>> is_palindrome("RaceCar")
    True
    >>> is_palindrome("python")
    False
    """
    normalized = text.lower()
    return normalized == normalized[::-1]

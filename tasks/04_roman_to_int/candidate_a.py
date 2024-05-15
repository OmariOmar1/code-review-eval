"""Roman numeral parsing."""

VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_int(numeral):
    """Convert a valid Roman numeral to an integer.

    A symbol smaller than the one after it is subtracted, otherwise added.

    >>> roman_to_int("III")
    3
    >>> roman_to_int("IV")
    4
    >>> roman_to_int("MCMXCIV")
    1994
    """
    total = 0
    for symbol, following in zip(numeral, numeral[1:] + " "):
        value = VALUES[symbol]
        if value < VALUES.get(following, 0):
            total -= value
        else:
            total += value
    return total

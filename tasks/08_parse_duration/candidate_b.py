import re


def parse_duration(text):
    """Parse a duration string into seconds.

    >>> parse_duration("1h30m")
    5400
    """
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    total = 0
    for amount, unit in re.findall(r"(\d+)([dhms])", text.lower()):
        total += int(amount) * units[unit]
    return total

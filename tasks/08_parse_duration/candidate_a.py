"""Duration string parsing."""

import re

SECONDS_PER_UNIT = {"d": 86400, "h": 3600, "m": 60, "s": 1}
GROUP = re.compile(r"(\d+)([dhms])")
FULL = re.compile(r"(?:\d+[dhms]\s*)+")


def parse_duration(text):
    """Convert a string like ``"1h30m"`` to seconds.

    Raises ``ValueError`` unless the whole string is made of
    ``<integer><unit>`` groups.

    >>> parse_duration("1h30m")
    5400
    >>> parse_duration(" 2H 15M ")
    8100
    >>> parse_duration("0s")
    0
    >>> parse_duration("1h30")
    Traceback (most recent call last):
        ...
    ValueError: invalid duration: '1h30'
    """
    cleaned = text.strip().lower()
    if not FULL.fullmatch(cleaned):
        raise ValueError(f"invalid duration: {text!r}")
    return sum(
        int(amount) * SECONDS_PER_UNIT[unit] for amount, unit in GROUP.findall(cleaned)
    )

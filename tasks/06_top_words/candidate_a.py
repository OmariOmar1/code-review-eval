"""Word frequency helper."""

import re
from collections import Counter

WORD_PATTERN = re.compile(r"[a-z']+")


def top_words(text, n):
    """Return the ``n`` most common words as ``(word, count)`` tuples.

    Ordering is by count descending, then alphabetically, so results are
    stable for equal counts.

    >>> top_words("Hello, world! Hello.", 2)
    [('hello', 2), ('world', 1)]
    >>> top_words("pear apple", 2)
    [('apple', 1), ('pear', 1)]
    >>> top_words("anything", 0)
    []
    >>> top_words("", 5)
    []
    """
    if n <= 0:
        return []
    counts = Counter(WORD_PATTERN.findall(text.lower()))
    ranked = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    return ranked[:n]

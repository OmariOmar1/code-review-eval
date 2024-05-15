from collections import Counter


def top_words(text, n):
    """Count words and return the most common ones.

    >>> top_words("a b a", 1)
    [('a', 2)]
    """
    words = text.lower().split()
    return Counter(words).most_common(n)

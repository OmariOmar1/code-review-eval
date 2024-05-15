"""Utilities for splitting sequences into fixed-size pieces."""

from typing import List, Sequence, TypeVar

T = TypeVar("T")


def chunk(items: Sequence[T], size: int) -> List[List[T]]:
    """Split ``items`` into consecutive chunks of ``size`` elements.

    Raises ``ValueError`` when ``size`` is not a positive integer.

    >>> chunk([1, 2, 3, 4], 2)
    [[1, 2], [3, 4]]
    >>> chunk([1, 2, 3], 1)
    [[1], [2], [3]]
    >>> chunk([], 3)
    []
    >>> chunk([1, 2, 3], 0)
    Traceback (most recent call last):
        ...
    ValueError: size must be at least 1
    """
    if size < 1:
        raise ValueError("size must be at least 1")
    chunks = []
    for start in range(0, len(items) - size + 1, size):
        chunks.append(list(items[start:start + size]))
    return chunks

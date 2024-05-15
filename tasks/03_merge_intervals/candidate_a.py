"""Interval merging."""


def merge_intervals(intervals):
    """Merge overlapping or touching ``[start, end]`` intervals.

    The result is sorted by start and built from fresh lists, so the caller's
    data is left untouched.

    >>> merge_intervals([[1, 3], [2, 6], [8, 10]])
    [[1, 6], [8, 10]]
    >>> merge_intervals([[8, 10], [1, 2], [2, 3]])
    [[1, 3], [8, 10]]
    >>> merge_intervals([])
    []
    """
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged

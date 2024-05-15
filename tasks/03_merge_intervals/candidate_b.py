def merge_intervals(intervals):
    """Merge intervals that overlap.

    >>> merge_intervals([[1, 3], [2, 6], [8, 10]])
    [[1, 6], [8, 10]]
    """
    result = []
    for interval in intervals:
        if len(result) > 0 and interval[0] <= result[-1][1]:
            result[-1][1] = max(result[-1][1], interval[1])
        else:
            result.append(interval)
    return result

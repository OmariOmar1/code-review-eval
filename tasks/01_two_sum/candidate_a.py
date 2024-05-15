"""Find the pair of indices whose values add up to a target."""


def two_sum(nums, target):
    """Return indices ``(i, j)``, ``i < j``, with ``nums[i] + nums[j] == target``.

    Returns ``None`` when no pair exists. Runs in a single pass by remembering
    the index of every value seen so far.

    >>> two_sum([2, 7, 11, 15], 9)
    (0, 1)
    >>> two_sum([3, 3], 6)
    (0, 1)
    >>> two_sum([3, 2, 5], 6) is None
    True
    >>> two_sum([], 1) is None
    True
    """
    seen = {}
    for index, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return (seen[complement], index)
        seen[value] = index
    return None

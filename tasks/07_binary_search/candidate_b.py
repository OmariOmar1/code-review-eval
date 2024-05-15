def binary_search(items, target):
    """Return the index of ``target`` in sorted ``items``, or -1 if absent.

    ``low`` and ``high`` are inclusive bounds, so an empty list never enters
    the loop.

    >>> binary_search([1, 3, 5, 7, 9], 9)
    4
    >>> binary_search([1, 3, 5], 10)
    -1
    >>> binary_search([], 1)
    -1
    """
    low, high = 0, len(items) - 1
    while low <= high:
        middle = (low + high) // 2
        if items[middle] == target:
            return middle
        if items[middle] < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1

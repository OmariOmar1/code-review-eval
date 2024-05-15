"""Binary search."""


def binary_search(items, target):
    """Return the index of ``target`` in sorted ``items``, or -1.

    >>> binary_search([1, 3, 5, 7, 9], 5)
    2
    >>> binary_search([1, 3, 5, 7, 9], 4)
    -1
    """
    low = 0
    high = len(items)
    while low <= high:
        middle = (low + high) // 2
        if items[middle] == target:
            return middle
        if items[middle] < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1

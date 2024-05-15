"""Flatten helper."""


def flatten(nested):
    """Flatten a list that contains other lists.

    >>> flatten([1, [2, 3], 4])
    [1, 2, 3, 4]
    >>> flatten([])
    []
    """
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(item)
        else:
            flat.append(item)
    return flat

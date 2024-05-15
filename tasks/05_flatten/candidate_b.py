def flatten(nested):
    """Recursively flatten lists and tuples; strings stay whole.

    >>> flatten([1, [2, [3, [4]]]])
    [1, 2, 3, 4]
    >>> flatten([(1, 2), "ab"])
    [1, 2, 'ab']
    >>> flatten([[], [[]]])
    []
    """
    flat = []
    for item in nested:
        if isinstance(item, (list, tuple)):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat

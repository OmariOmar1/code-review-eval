from solution import flatten


def test_already_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]


def test_empty():
    assert flatten([]) == []


def test_one_level():
    assert flatten([1, [2, 3], 4]) == [1, 2, 3, 4]


def test_deeply_nested():
    assert flatten([1, [2, [3, [4, [5]]]]]) == [1, 2, 3, 4, 5]


def test_tuples_are_flattened():
    assert flatten([(1, 2), [3, (4,)]]) == [1, 2, 3, 4]


def test_strings_are_atoms():
    assert flatten(["ab", ["cd", ["ef"]]]) == ["ab", "cd", "ef"]


def test_empty_sublists():
    assert flatten([[], [[]], [1, []]]) == [1]


def test_returns_new_list():
    data = [1, 2]
    assert flatten(data) is not data

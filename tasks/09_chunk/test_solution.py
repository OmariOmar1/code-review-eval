import pytest

from solution import chunk


def test_even_split():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_uneven_split_keeps_remainder():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_size_larger_than_list():
    assert chunk([1, 2], 5) == [[1, 2]]


def test_size_one():
    assert chunk([1, 2, 3], 1) == [[1], [2], [3]]


def test_empty_list():
    assert chunk([], 3) == []


def test_exact_size():
    assert chunk([1, 2, 3], 3) == [[1, 2, 3]]


@pytest.mark.parametrize("size", [0, -1])
def test_invalid_size(size):
    with pytest.raises(ValueError):
        chunk([1, 2, 3], size)

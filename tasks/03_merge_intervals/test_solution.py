import copy

from solution import merge_intervals


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[1, 3]]) == [[1, 3]]


def test_overlapping():
    assert merge_intervals([[1, 3], [2, 6], [8, 10]]) == [[1, 6], [8, 10]]


def test_touching_intervals_merge():
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_contained_interval():
    assert merge_intervals([[1, 10], [2, 3], [4, 5]]) == [[1, 10]]


def test_disjoint_stay_separate():
    assert merge_intervals([[5, 6], [1, 2]]) == [[1, 2], [5, 6]]


def test_input_not_mutated():
    data = [[1, 4], [2, 6], [0, 0]]
    snapshot = copy.deepcopy(data)
    merge_intervals(data)
    assert data == snapshot

import pytest

from solution import binary_search


def test_found_middle():
    assert binary_search([1, 3, 5, 7, 9], 5) == 2


def test_found_first_and_last():
    assert binary_search([1, 3, 5, 7, 9], 1) == 0
    assert binary_search([1, 3, 5, 7, 9], 9) == 4


def test_missing_in_range():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1


def test_missing_below_range():
    assert binary_search([1, 3, 5], 0) == -1


def test_missing_above_range():
    assert binary_search([1, 3, 5], 10) == -1


def test_empty_list():
    assert binary_search([], 1) == -1


def test_single_element():
    assert binary_search([4], 4) == 0
    assert binary_search([4], 5) == -1


@pytest.mark.parametrize("target", range(0, 200, 7))
def test_every_position(target):
    items = list(range(0, 200, 7))
    assert binary_search(items, target) == target // 7

import pytest

from solution import two_sum


def test_basic_pair():
    assert two_sum([2, 7, 11, 15], 9) == (0, 1)


def test_pair_at_end():
    assert two_sum([1, 2, 3, 4], 7) == (2, 3)


def test_negative_numbers():
    assert two_sum([-3, 4, 3, 90], 0) == (0, 2)


def test_duplicates_form_pair():
    assert two_sum([3, 3], 6) == (0, 1)


def test_same_element_not_reused():
    assert two_sum([3, 2, 5], 6) is None


def test_no_pair():
    assert two_sum([1, 2, 3], 100) is None


@pytest.mark.parametrize("nums", [[], [5]])
def test_too_short(nums):
    assert two_sum(nums, 5) is None


def test_large_input():
    nums = list(range(3000))
    assert two_sum(nums, 5997) == (2998, 2999)

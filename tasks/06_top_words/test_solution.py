from solution import top_words


def test_basic_counts():
    assert top_words("a b a c a b", 2) == [("a", 3), ("b", 2)]


def test_case_insensitive():
    assert top_words("The the THE cat", 1) == [("the", 3)]


def test_punctuation_is_stripped():
    assert top_words("Hello, world! Hello.", 2) == [("hello", 2), ("world", 1)]


def test_ties_break_alphabetically():
    assert top_words("pear apple fig", 3) == [("apple", 1), ("fig", 1), ("pear", 1)]


def test_apostrophes_kept():
    assert top_words("don't stop, don't", 1) == [("don't", 2)]


def test_n_larger_than_vocabulary():
    assert top_words("one two", 10) == [("one", 1), ("two", 1)]


def test_empty_text():
    assert top_words("", 3) == []


def test_non_positive_n():
    assert top_words("a b c", 0) == []
    assert top_words("a b c", -2) == []

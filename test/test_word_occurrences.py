"""Tests for word-under-cursor detection and occurrence finding."""
from __future__ import annotations

from je_editor.utils.occurrence.word_occurrences import (
    find_occurrences,
    is_highlightable_word,
    word_at,
)


class TestWordAt:
    def test_inside_word(self):
        assert word_at("foo bar", 1) == ("foo", 0, 3)

    def test_at_word_start(self):
        assert word_at("foo bar", 4) == ("bar", 4, 7)

    def test_just_past_word_end(self):
        # Caret right after "foo" still resolves to "foo".
        assert word_at("foo bar", 3) == ("foo", 0, 3)

    def test_on_whitespace_returns_none(self):
        assert word_at("foo   bar", 4) is None

    def test_identifier_with_underscore(self):
        assert word_at("my_var = 1", 3) == ("my_var", 0, 6)

    def test_out_of_range_returns_none(self):
        assert word_at("foo", 99) is None

    def test_negative_returns_none(self):
        assert word_at("foo", -1) is None

    def test_empty_text(self):
        assert word_at("", 0) is None

    def test_number_is_part_of_identifier(self):
        assert word_at("var2 = 1", 0) == ("var2", 0, 4)


class TestIsHighlightableWord:
    def test_normal_identifier(self):
        assert is_highlightable_word("value")

    def test_single_char_rejected(self):
        assert not is_highlightable_word("x")

    def test_keyword_rejected(self):
        assert not is_highlightable_word("def")
        assert not is_highlightable_word("class")

    def test_non_identifier_rejected(self):
        assert not is_highlightable_word("a-b")
        assert not is_highlightable_word("123")

    def test_empty_rejected(self):
        assert not is_highlightable_word("")


class TestFindOccurrences:
    def test_finds_all_positions(self):
        text = "value = value + other_value"
        # 'value' at 0 and 8, but not inside 'other_value'
        assert find_occurrences(text, "value") == [0, 8]

    def test_whole_word_only(self):
        assert find_occurrences("values valuer value", "value") == [14]

    def test_no_match(self):
        assert find_occurrences("abc def", "xyz") == []

    def test_keyword_not_matched(self):
        assert find_occurrences("def foo(): def bar():", "def") == []

    def test_short_word_not_matched(self):
        assert find_occurrences("x = x + x", "x") == []

    def test_special_regex_chars_are_escaped(self):
        # A word that is not a valid identifier is rejected before regex use.
        assert find_occurrences("a.b a.b", "a.b") == []

    def test_multiline_text(self):
        text = "total = 1\nprint(total)\ntotal += 2"
        assert find_occurrences(text, "total") == [0, 16, 23]

    def test_underscored_identifier(self):
        text = "my_var = my_var + 1"
        assert find_occurrences(text, "my_var") == [0, 9]

"""Tests for pure bookmark navigation logic."""
from __future__ import annotations

from je_editor.utils.bookmark.bookmark_navigation import (
    next_bookmark,
    normalise_lines,
    prev_bookmark,
    toggle_line,
)


class TestNormaliseLines:
    def test_sorts_and_dedupes(self):
        assert normalise_lines([5, 1, 5, 3]) == [1, 3, 5]

    def test_empty(self):
        assert normalise_lines([]) == []


class TestNextBookmark:
    def test_finds_next(self):
        assert next_bookmark([2, 5, 9], 5) == 9

    def test_skips_current_line(self):
        assert next_bookmark([2, 5, 9], 4) == 5

    def test_wraps_to_first(self):
        assert next_bookmark([2, 5, 9], 9) == 2

    def test_no_wrap_returns_none_past_last(self):
        assert next_bookmark([2, 5, 9], 9, wrap=False) is None

    def test_empty_returns_none(self):
        assert next_bookmark([], 3) is None

    def test_before_first_returns_first(self):
        assert next_bookmark([4, 8], 1) == 4


class TestPrevBookmark:
    def test_finds_previous(self):
        assert prev_bookmark([2, 5, 9], 5) == 2

    def test_skips_current_line(self):
        assert prev_bookmark([2, 5, 9], 6) == 5

    def test_wraps_to_last(self):
        assert prev_bookmark([2, 5, 9], 2) == 9

    def test_no_wrap_returns_none_before_first(self):
        assert prev_bookmark([2, 5, 9], 2, wrap=False) is None

    def test_empty_returns_none(self):
        assert prev_bookmark([], 3) is None

    def test_after_last_returns_last(self):
        assert prev_bookmark([4, 8], 20) == 8


class TestToggleLine:
    def test_adds_when_absent(self):
        assert toggle_line([1, 3], 2) == [1, 2, 3]

    def test_removes_when_present(self):
        assert toggle_line([1, 2, 3], 2) == [1, 3]

    def test_toggle_twice_is_identity(self):
        once = toggle_line([1, 3], 5)
        twice = toggle_line(once, 5)
        assert twice == [1, 3]

    def test_result_is_sorted_and_unique(self):
        assert toggle_line([3, 1, 3], 2) == [1, 2, 3]

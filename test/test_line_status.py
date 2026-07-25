"""Tests for the line-by-line diff behind the editor's git change markers."""
from __future__ import annotations

from je_editor.utils.file_diff.line_status import (
    LINE_ADDED,
    LINE_MODIFIED,
    LINE_REMOVED_ABOVE,
    MAX_DIFFED_LINES,
    changed_line_numbers,
    line_statuses,
    next_changed_line,
    previous_changed_line,
)


class TestLineStatuses:
    def test_identical_text_has_no_markers(self):
        assert line_statuses("a\nb\nc\n", "a\nb\nc\n") == {}

    def test_appended_line_is_added(self):
        assert line_statuses("a\nb\n", "a\nb\nc\n") == {2: LINE_ADDED}

    def test_inserted_line_is_added(self):
        assert line_statuses("a\nc\n", "a\nb\nc\n") == {1: LINE_ADDED}

    def test_changed_line_is_modified(self):
        assert line_statuses("a\nb\nc\n", "a\nB\nc\n") == {1: LINE_MODIFIED}

    def test_several_changed_lines_are_each_modified(self):
        statuses = line_statuses("a\nb\nc\n", "a\nB\nC\n")
        assert statuses == {1: LINE_MODIFIED, 2: LINE_MODIFIED}

    def test_deleted_line_marks_the_line_below(self):
        assert line_statuses("a\nb\nc\n", "a\nc\n") == {1: LINE_REMOVED_ABOVE}

    def test_deletion_at_the_end_marks_the_last_line(self):
        assert line_statuses("a\nb\nc\n", "a\nb\n") == {1: LINE_REMOVED_ABOVE}

    def test_new_file_marks_every_line_added(self):
        assert line_statuses("", "a\nb\n") == {0: LINE_ADDED, 1: LINE_ADDED}

    def test_emptied_file_has_no_lines_to_mark(self):
        assert line_statuses("a\nb\n", "") == {}

    def test_both_empty(self):
        assert line_statuses("", "") == {}

    def test_a_real_status_is_not_overwritten_by_a_deletion_marker(self):
        # "b" and "c" are gone and "d" is new: the new line keeps its own status.
        statuses = line_statuses("a\nb\nc\n", "a\nd\n")
        assert statuses[1] in {LINE_MODIFIED, LINE_ADDED}

    def test_no_trailing_newline_is_handled(self):
        assert line_statuses("a\nb", "a\nB") == {1: LINE_MODIFIED}

    def test_leading_insertion(self):
        assert line_statuses("b\n", "a\nb\n") == {0: LINE_ADDED}

    def test_indentation_only_change_counts_as_modified(self):
        assert line_statuses("x = 1\n", "    x = 1\n") == {0: LINE_MODIFIED}

    def test_oversized_buffer_is_skipped(self):
        big = "\n".join(str(number) for number in range(MAX_DIFFED_LINES + 5))
        assert line_statuses("a\n", big) == {}

    def test_oversized_baseline_is_skipped(self):
        big = "\n".join(str(number) for number in range(MAX_DIFFED_LINES + 5))
        assert line_statuses(big, "a\n") == {}


class TestChangedLineNumbers:
    def test_sorted_ascending(self):
        statuses = {5: LINE_ADDED, 1: LINE_MODIFIED, 3: LINE_ADDED}
        assert changed_line_numbers(statuses) == [1, 3, 5]

    def test_empty(self):
        assert changed_line_numbers({}) == []


class TestChangeNavigation:
    def _statuses(self):
        return {2: LINE_ADDED, 5: LINE_MODIFIED, 9: LINE_ADDED}

    def test_next_from_before_the_first(self):
        assert next_changed_line(self._statuses(), 0) == 2

    def test_next_skips_the_current_line(self):
        assert next_changed_line(self._statuses(), 2) == 5

    def test_next_wraps_around(self):
        assert next_changed_line(self._statuses(), 20) == 2

    def test_previous_from_after_the_last(self):
        assert previous_changed_line(self._statuses(), 20) == 9

    def test_previous_skips_the_current_line(self):
        assert previous_changed_line(self._statuses(), 5) == 2

    def test_previous_wraps_around(self):
        assert previous_changed_line(self._statuses(), 0) == 9

    def test_no_changes_yields_none(self):
        assert next_changed_line({}, 3) is None
        assert previous_changed_line({}, 3) is None

    def test_single_change_returns_itself_when_wrapping(self):
        assert next_changed_line({4: LINE_ADDED}, 4) == 4
        assert previous_changed_line({4: LINE_ADDED}, 4) == 4

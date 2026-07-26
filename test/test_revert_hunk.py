"""Tests for hunk detection and reverting a change back to its committed form."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.file_diff.line_status import (
    baseline_lines_of,
    hunk_at_line,
    hunks,
)


class TestHunks:
    def test_no_change_has_no_hunks(self):
        assert hunks("a\nb\n", "a\nb\n") == []

    def test_a_modified_line(self):
        found = hunks("a\nb\nc\n", "a\nB\nc\n")
        assert len(found) == 1
        assert (found[0].start, found[0].end) == (1, 2)
        assert (found[0].baseline_start, found[0].baseline_end) == (1, 2)

    def test_an_inserted_line_spans_no_baseline(self):
        found = hunks("a\nc\n", "a\nb\nc\n")
        assert (found[0].start, found[0].end) == (1, 2)
        assert found[0].baseline_start == found[0].baseline_end

    def test_a_deleted_line_spans_no_current_lines(self):
        found = hunks("a\nb\nc\n", "a\nc\n")
        assert found[0].is_pure_deletion
        assert (found[0].baseline_start, found[0].baseline_end) == (1, 2)

    def test_several_hunks_are_reported_in_order(self):
        found = hunks("a\nb\nc\nd\n", "A\nb\nc\nD\n")
        assert [hunk.start for hunk in found] == [0, 3]

    def test_hunk_at_line_finds_the_containing_hunk(self):
        hunk = hunk_at_line("a\nb\nc\n", "a\nB\nc\n", 1)
        assert hunk is not None and hunk.start == 1

    def test_hunk_at_an_unchanged_line(self):
        assert hunk_at_line("a\nb\nc\n", "a\nB\nc\n", 0) is None

    def test_hunk_at_a_deletion_point(self):
        hunk = hunk_at_line("a\nb\nc\n", "a\nc\n", 1)
        assert hunk is not None and hunk.is_pure_deletion

    def test_baseline_lines_of_a_hunk(self):
        hunk = hunk_at_line("a\nold\nc\n", "a\nnew\nc\n", 1)
        assert baseline_lines_of("a\nold\nc\n", hunk) == ["old"]

    def test_baseline_lines_of_an_insertion_is_empty(self):
        hunk = hunk_at_line("a\nc\n", "a\nb\nc\n", 1)
        assert baseline_lines_of("a\nc\n", hunk) == []


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def editor(app):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        code_editor = CodeEditor(parent)
    yield code_editor
    code_editor.lint_manager.stop()
    code_editor.diff_marker_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


def _place_cursor(editor, line: int) -> None:
    block = editor.document().findBlockByNumber(line)
    cursor = editor.textCursor()
    cursor.setPosition(block.position())
    editor.setTextCursor(cursor)


class TestRevertChange:
    def test_modified_line_goes_back_to_the_committed_text(self, editor):
        editor.setPlainText("a\nCHANGED\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 1)
        assert editor.revert_change_at_cursor() is True
        assert editor.toPlainText() == "a\nb\nc\n"

    def test_added_line_is_removed(self, editor):
        editor.setPlainText("a\nextra\nb\n")
        editor.diff_marker_manager.set_baseline("a\nb\n")
        _place_cursor(editor, 1)
        assert editor.revert_change_at_cursor() is True
        assert editor.toPlainText() == "a\nb\n"

    def test_deleted_line_comes_back(self, editor):
        editor.setPlainText("a\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 1)
        assert editor.revert_change_at_cursor() is True
        assert editor.toPlainText() == "a\nb\nc\n"

    def test_only_the_hunk_under_the_caret_is_reverted(self, editor):
        editor.setPlainText("A\nb\nC\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 0)
        editor.revert_change_at_cursor()
        assert editor.toPlainText() == "a\nb\nC\n"

    def test_reverting_an_unchanged_line_does_nothing(self, editor):
        editor.setPlainText("a\nB\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 0)
        assert editor.revert_change_at_cursor() is False
        assert editor.toPlainText() == "a\nB\nc\n"

    def test_reverting_without_a_baseline_does_nothing(self, editor):
        editor.setPlainText("a\nb\n")
        _place_cursor(editor, 0)
        assert editor.revert_change_at_cursor() is False

    def test_revert_is_a_single_undo_step(self, editor):
        editor.setPlainText("a\nCHANGED\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 1)
        editor.revert_change_at_cursor()
        editor.undo()
        assert editor.toPlainText() == "a\nCHANGED\nc\n"

    def test_markers_are_updated_after_a_revert(self, editor):
        editor.setPlainText("a\nCHANGED\nc\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\n")
        _place_cursor(editor, 1)
        editor.revert_change_at_cursor()
        assert editor.diff_marker_manager.statuses() == {}

    def test_added_line_at_the_end_of_file_is_removed(self, editor):
        editor.setPlainText("a\nb\nextra")
        editor.diff_marker_manager.set_baseline("a\nb")
        _place_cursor(editor, 2)
        assert editor.revert_change_at_cursor() is True
        assert editor.toPlainText() == "a\nb"

    def test_reverting_a_multi_line_hunk(self, editor):
        editor.setPlainText("a\nX\nY\nd\n")
        editor.diff_marker_manager.set_baseline("a\nb\nc\nd\n")
        _place_cursor(editor, 1)
        assert editor.revert_change_at_cursor() is True
        assert editor.toPlainText() == "a\nb\nc\nd\n"

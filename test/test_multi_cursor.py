"""Tests for multiple carets: position bookkeeping and editing at each."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication

from je_editor.utils.multi_cursor.cursor_positions import (
    add_position,
    clamp_positions,
    remove_position,
    shift_after_delete,
    shift_after_insert,
    toggle_position,
)


class TestPositionBookkeeping:
    def test_adding_keeps_them_sorted(self):
        assert add_position([5, 1], 3) == [1, 3, 5]

    def test_adding_a_duplicate_changes_nothing(self):
        assert add_position([1, 3], 3) == [1, 3]

    def test_negative_positions_are_refused(self):
        assert add_position([1], -5) == [1]

    def test_removing(self):
        assert remove_position([1, 3, 5], 3) == [1, 5]

    def test_removing_an_absent_position(self):
        assert remove_position([1, 5], 3) == [1, 5]

    def test_toggle_adds_then_removes(self):
        positions = toggle_position([], 4)
        assert positions == [4]
        assert toggle_position(positions, 4) == []


class TestShifting:
    def test_insert_moves_later_positions(self):
        assert shift_after_insert([2, 10], 5, 3) == [2, 13]

    def test_insert_at_a_position_leaves_it_alone(self):
        assert shift_after_insert([5], 5, 3) == [5]

    def test_delete_moves_later_positions_back(self):
        assert shift_after_delete([2, 10], 5, 3) == [2, 7]

    def test_delete_collapses_positions_inside_the_range(self):
        assert shift_after_delete([6], 5, 3) == [5]

    def test_delete_leaves_earlier_positions_alone(self):
        assert shift_after_delete([2], 5, 3) == [2]

    def test_clamping_to_the_document(self):
        assert clamp_positions([-2, 5, 99], 10) == [0, 5, 10]

    def test_clamping_deduplicates(self):
        assert clamp_positions([12, 15], 10) == [10]

    def test_clamping_an_empty_document(self):
        assert clamp_positions([3], -1) == []


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
    code_editor.blame_manager.stop()
    code_editor.close()
    code_editor.deleteLater()


def _select_all(editor) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(editor.document().characterCount() - 1, cursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


def _type(editor, text: str) -> None:
    editor.keyPressEvent(
        QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, text))


class TestMultiCursorEditing:
    def test_no_extra_cursors_at_first(self, editor):
        assert editor.multi_cursor_manager.active is False

    def test_cursors_are_added_to_each_selected_line(self, editor):
        editor.setPlainText("one\ntwo\nthree\n")
        _select_all(editor)
        added = editor.add_cursors_to_selected_lines()
        assert added >= 1
        assert editor.multi_cursor_manager.active

    def test_typing_reaches_every_line(self, editor):
        editor.setPlainText("one\ntwo\nthree")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        _type(editor, ",")
        assert editor.toPlainText() == "one,\ntwo,\nthree,"

    def test_typing_several_characters(self, editor):
        editor.setPlainText("a\nb")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        _type(editor, "x")
        _type(editor, "y")
        assert editor.toPlainText() == "axy\nbxy"

    def test_backspace_reaches_every_line(self, editor):
        editor.setPlainText("one!\ntwo!\nthree!")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        editor.keyPressEvent(QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier))
        assert editor.toPlainText() == "one\ntwo\nthree"

    def test_multi_cursor_edit_is_one_undo_step(self, editor):
        editor.setPlainText("one\ntwo")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        _type(editor, ";")
        editor.undo()
        assert editor.toPlainText() == "one\ntwo"

    def test_escape_clears_the_extra_cursors(self, editor):
        editor.setPlainText("one\ntwo")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        editor.keyPressEvent(QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
        assert editor.multi_cursor_manager.active is False

    def test_clearing_leaves_typing_to_the_primary_caret(self, editor):
        editor.setPlainText("one\ntwo")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        editor.clear_extra_cursors()
        _type(editor, "!")
        assert editor.toPlainText().count("!") == 1

    def test_adding_without_a_selection_does_nothing(self, editor):
        editor.setPlainText("one\ntwo")
        assert editor.add_cursors_to_selected_lines() == 0

    def test_toggling_the_same_position_twice_removes_it(self, editor):
        editor.setPlainText("hello")
        editor.multi_cursor_manager.toggle_at(2)
        assert editor.multi_cursor_manager.positions() == [2]
        editor.multi_cursor_manager.toggle_at(2)
        assert editor.multi_cursor_manager.positions() == []

    def test_backspace_at_the_document_start_is_refused(self, editor):
        editor.setPlainText("abc")
        editor.multi_cursor_manager.toggle_at(0)
        cursor = editor.textCursor()
        cursor.setPosition(2)
        editor.setTextCursor(cursor)
        assert editor.multi_cursor_manager.delete_before() is False
        assert editor.toPlainText() == "abc"

    def test_painting_extra_cursors_does_not_raise(self, editor):
        editor.setPlainText("one\ntwo\nthree")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        editor.show()
        QApplication.processEvents()
        editor.hide()

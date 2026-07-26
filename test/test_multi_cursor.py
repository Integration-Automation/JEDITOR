"""Tests for multiple carets: position bookkeeping and editing at each."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from je_editor.utils.multi_cursor.cursor_positions import (
    add_position,
    clamp_positions,
    column_caret_columns,
    column_span,
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


class TestColumnGeometry:
    def test_span_downwards(self):
        assert list(column_span(2, 5)) == [2, 3, 4, 5]

    def test_span_upwards_is_the_same_range(self):
        assert list(column_span(5, 2)) == [2, 3, 4, 5]

    def test_span_of_one_line(self):
        assert list(column_span(3, 3)) == [3]

    def test_columns_follow_the_pointer(self):
        assert column_caret_columns(2, 6, [10, 10, 10]) == [6, 6, 6]

    def test_a_short_line_stops_at_its_end(self):
        assert column_caret_columns(2, 6, [10, 3, 10]) == [6, 3, 6]

    def test_dragging_straight_down_keeps_the_anchor_column(self):
        assert column_caret_columns(4, 4, [10, 10]) == [4, 4]

    def test_no_lines_covered(self):
        assert column_caret_columns(0, 3, []) == []


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
    """Send a keystroke the way Qt does, so it owns the event object.

    Building a QKeyEvent in Python and handing it to the handler leaves Qt
    holding an object Python may collect, which crashes the interpreter later
    when the event queue is processed.
    """
    QTest.keyClicks(editor, text)


def _press(editor, key) -> None:
    """Send one non-printable key."""
    QTest.keyClick(editor, key)


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
        _press(editor, Qt.Key.Key_Backspace)
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
        _press(editor, Qt.Key.Key_Escape)
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

    def test_delete_reaches_every_line(self, editor):
        editor.setPlainText("one!\ntwo!\nthree!")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        # Each caret sits at its line end, so step back one to sit before the "!".
        # move_all takes the primary caret with it, so no separate nudge is needed.
        editor.multi_cursor_manager.move_all(-1)
        _press(editor, Qt.Key.Key_Delete)
        assert editor.toPlainText() == "one\ntwo\nthree"

    def test_delete_at_the_document_end_is_refused(self, editor):
        editor.setPlainText("abc")
        editor.multi_cursor_manager.toggle_at(3)
        assert editor.multi_cursor_manager.delete_after() is False
        assert editor.toPlainText() == "abc"

    def test_enter_splits_every_line(self, editor):
        editor.setPlainText("ab\ncd")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        _press(editor, Qt.Key.Key_Return)
        assert editor.toPlainText() == "ab\n\ncd\n"

    def test_arrow_keys_move_the_extra_carets(self, editor):
        editor.setPlainText("hello world")
        editor.multi_cursor_manager.toggle_at(5)
        _press(editor, Qt.Key.Key_Right)
        assert editor.multi_cursor_manager.positions() == [6]
        _press(editor, Qt.Key.Key_Left)
        assert editor.multi_cursor_manager.positions() == [5]

    def test_the_primary_caret_moves_along(self, editor):
        # It used to stay behind, so one arrow press pulled the carets apart.
        editor.setPlainText("hello world")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor.multi_cursor_manager.toggle_at(5)
        _press(editor, Qt.Key.Key_Right)
        assert editor.textCursor().position() == 1

    def test_down_moves_every_caret_a_line(self, editor):
        editor.setPlainText("alpha\nbravo\ncharlie")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        editor.multi_cursor_manager.toggle_at(3)
        _press(editor, Qt.Key.Key_Down)
        assert editor.multi_cursor_manager.positions() == [9]
        assert editor.textCursor().position() == 7

    def test_up_moves_every_caret_a_line(self, editor):
        editor.setPlainText("alpha\nbravo")
        editor.multi_cursor_manager.toggle_at(8)
        _press(editor, Qt.Key.Key_Up)
        assert editor.multi_cursor_manager.positions() == [2]

    def test_a_caret_past_a_shorter_line_stops_at_its_end(self, editor):
        editor.setPlainText("longer line\nab")
        editor.multi_cursor_manager.toggle_at(9)
        _press(editor, Qt.Key.Key_Down)
        assert editor.multi_cursor_manager.positions() == [14]

    def test_moving_past_the_last_line_drops_nothing(self, editor):
        editor.setPlainText("only")
        editor.multi_cursor_manager.toggle_at(2)
        _press(editor, Qt.Key.Key_Down)
        assert editor.multi_cursor_manager.positions() == [2]

    def test_end_sends_every_caret_to_its_line_end(self, editor):
        editor.setPlainText("alpha\nbravo")
        editor.multi_cursor_manager.toggle_at(1)
        cursor = editor.textCursor()
        cursor.setPosition(7)
        editor.setTextCursor(cursor)
        _press(editor, Qt.Key.Key_End)
        assert editor.multi_cursor_manager.positions() == [5]
        assert editor.textCursor().position() == 11

    def test_home_sends_every_caret_to_its_line_start(self, editor):
        editor.setPlainText("alpha\nbravo")
        editor.multi_cursor_manager.toggle_at(4)
        cursor = editor.textCursor()
        cursor.setPosition(9)
        editor.setTextCursor(cursor)
        _press(editor, Qt.Key.Key_Home)
        assert editor.multi_cursor_manager.positions() == [0]
        assert editor.textCursor().position() == 6

    def test_vertical_movement_needs_extra_carets(self, editor):
        editor.setPlainText("alpha\nbravo")
        assert editor.multi_cursor_manager.move_all_vertically(1) is False

    def test_carets_never_move_outside_the_document(self, editor):
        editor.setPlainText("ab")
        editor.multi_cursor_manager.toggle_at(0)
        editor.multi_cursor_manager.move_all(-5)
        assert editor.multi_cursor_manager.positions() == [0]
        editor.multi_cursor_manager.move_all(99)
        assert editor.multi_cursor_manager.positions() == [2]

    def test_a_caret_can_be_added_on_the_line_below(self, editor):
        editor.setPlainText("alpha\nbeta\ngamma")
        cursor = editor.textCursor()
        cursor.setPosition(2)
        editor.setTextCursor(cursor)
        assert editor.add_cursor_below() is True
        assert editor.multi_cursor_manager.positions() == [8]

    def test_a_caret_can_be_added_on_the_line_above(self, editor):
        editor.setPlainText("alpha\nbeta\ngamma")
        cursor = editor.textCursor()
        cursor.setPosition(8)
        editor.setTextCursor(cursor)
        assert editor.add_cursor_above() is True
        assert editor.multi_cursor_manager.positions() == [2]

    def test_no_caret_beyond_the_first_or_last_line(self, editor):
        editor.setPlainText("only one line")
        assert editor.add_cursor_above() is False
        assert editor.add_cursor_below() is False

    def test_a_short_line_clamps_the_column(self, editor):
        editor.setPlainText("longer line\nab")
        cursor = editor.textCursor()
        cursor.setPosition(9)
        editor.setTextCursor(cursor)
        editor.add_cursor_below()
        assert editor.multi_cursor_manager.positions() == [14]

    def test_next_occurrence_adds_a_caret(self, editor):
        editor.setPlainText("name = name + name")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        assert editor.add_cursor_at_next_occurrence() is True
        assert editor.multi_cursor_manager.positions() == [11]

    def test_next_occurrence_of_a_unique_word_wraps_to_itself(self, editor):
        editor.setPlainText("unique word")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        editor.add_cursor_at_next_occurrence()
        assert editor.multi_cursor_manager.positions() == [6]

    def test_next_occurrence_without_a_word_does_nothing(self, editor):
        editor.setPlainText("   ")
        cursor = editor.textCursor()
        cursor.setPosition(1)
        editor.setTextCursor(cursor)
        assert editor.add_cursor_at_next_occurrence() is False

    def test_typing_after_next_occurrence_changes_both(self, editor):
        editor.setPlainText("name = name")
        cursor = editor.textCursor()
        cursor.setPosition(4)
        editor.setTextCursor(cursor)
        editor.add_cursor_at_next_occurrence()
        _type(editor, "s")
        assert editor.toPlainText() == "names = names"

    def test_column_selection_puts_a_caret_on_each_line(self, editor):
        editor.setPlainText("alpha\nbeta\ngamma")
        # Drag from column 2 of line 0 to column 2 of line 2.
        extra = editor.multi_cursor_manager.select_column(2, 14)
        assert extra == 2
        assert editor.textCursor().blockNumber() == 2

    def test_column_selection_covers_every_line_between(self, editor):
        editor.setPlainText("alpha\nbeta\ngamma")
        editor.multi_cursor_manager.select_column(2, 14)
        lines = {
            editor.document().findBlock(position).blockNumber()
            for position in editor.multi_cursor_manager.positions()
        }
        assert lines == {0, 1}

    def test_column_selection_clamps_short_lines(self, editor):
        editor.setPlainText("a longer line\nab\nanother line")
        editor.multi_cursor_manager.select_column(8, 8 + 14 + 8)
        for position in editor.multi_cursor_manager.positions():
            block = editor.document().findBlock(position)
            assert position - block.position() <= len(block.text())

    def test_dragging_upwards_works_the_same(self, editor):
        editor.setPlainText("alpha\nbeta\ngamma")
        assert editor.multi_cursor_manager.select_column(14, 2) == 2
        assert editor.textCursor().blockNumber() == 0

    def test_typing_after_a_column_selection_edits_each_line(self, editor):
        editor.setPlainText("aaa\nbbb\nccc")
        editor.multi_cursor_manager.select_column(0, 8)
        _type(editor, "-")
        assert editor.toPlainText() == "-aaa\n-bbb\n-ccc"

    def test_painting_extra_cursors_does_not_raise(self, editor):
        editor.setPlainText("one\ntwo\nthree")
        _select_all(editor)
        editor.add_cursors_to_selected_lines()
        editor.show()
        QApplication.processEvents()
        editor.hide()

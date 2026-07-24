"""Tests for reverse_lines and the selected-line editor operations."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.line_ops.line_operations import reverse_lines


class TestReverseLines:
    def test_reverses_order(self):
        assert reverse_lines(["a", "b", "c"]) == ["c", "b", "a"]

    def test_single_line(self):
        assert reverse_lines(["only"]) == ["only"]

    def test_empty(self):
        assert reverse_lines([]) == []

    def test_does_not_mutate_input(self):
        original = ["a", "b"]
        reverse_lines(original)
        assert original == ["a", "b"]


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
    code_editor.close()
    code_editor.deleteLater()


def _select_lines(editor, start_line: int, end_line: int) -> None:
    document = editor.document()
    cursor = editor.textCursor()
    cursor.setPosition(document.findBlockByNumber(start_line).position())
    end_block = document.findBlockByNumber(end_line)
    cursor.setPosition(
        end_block.position() + end_block.length() - 1, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestRemoveDuplicateSelectedLines:
    def test_removes_duplicates(self, editor):
        editor.setPlainText("a\nb\na\nc\nb")
        _select_lines(editor, 0, 4)
        editor.remove_duplicate_selected_lines()
        assert editor.toPlainText() == "a\nb\nc"

    def test_keeps_first_occurrence_order(self, editor):
        editor.setPlainText("z\na\nz")
        _select_lines(editor, 0, 2)
        editor.remove_duplicate_selected_lines()
        assert editor.toPlainText() == "z\na"

    def test_single_line_is_noop(self, editor):
        editor.setPlainText("only")
        editor.remove_duplicate_selected_lines()
        assert editor.toPlainText() == "only"


class TestReverseSelectedLines:
    def test_reverses_selection(self, editor):
        editor.setPlainText("a\nb\nc")
        _select_lines(editor, 0, 2)
        editor.reverse_selected_lines()
        assert editor.toPlainText() == "c\nb\na"

    def test_reverses_partial_selection(self, editor):
        editor.setPlainText("a\nb\nc\nd")
        _select_lines(editor, 1, 2)
        editor.reverse_selected_lines()
        assert editor.toPlainText() == "a\nc\nb\nd"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("a\nb\nc")
        _select_lines(editor, 0, 2)
        editor.reverse_selected_lines()
        editor.undo()
        assert editor.toPlainText() == "a\nb\nc"

    def test_single_line_is_noop(self, editor):
        editor.setPlainText("only")
        editor.reverse_selected_lines()
        assert editor.toPlainText() == "only"


class TestNaturalSortSelectedLines:
    def test_natural_sort(self, editor):
        editor.setPlainText("item10\nitem2\nitem1")
        _select_lines(editor, 0, 2)
        editor.natural_sort_selected_lines()
        assert editor.toPlainText() == "item1\nitem2\nitem10"


class TestRemoveBlankSelectedLines:
    def test_removes_blank_lines(self, editor):
        editor.setPlainText("a\n\nb\n  \nc")
        _select_lines(editor, 0, 4)
        editor.remove_blank_selected_lines()
        assert editor.toPlainText() == "a\nb\nc"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("a\n\nb")
        _select_lines(editor, 0, 2)
        editor.remove_blank_selected_lines()
        editor.undo()
        assert editor.toPlainText() == "a\n\nb"

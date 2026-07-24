"""Tests for the enhanced duplicate command (line and selection)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication


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


class TestDuplicateLine:
    def test_duplicates_current_line_without_selection(self, editor):
        editor.setPlainText("aaa\nbbb")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        assert editor.toPlainText() == "aaa\naaa\nbbb"

    def test_line_duplicate_is_single_undo(self, editor):
        editor.setPlainText("aaa\nbbb")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        editor.undo()
        assert editor.toPlainText() == "aaa\nbbb"


class TestDuplicateSelection:
    def test_duplicates_selection_inline(self, editor):
        editor.setPlainText("abcdef")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)  # select "abc"
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        assert editor.toPlainText() == "abcabcdef"

    def test_caret_selects_the_new_copy(self, editor):
        editor.setPlainText("abcdef")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        assert editor.textCursor().selectedText() == "abc"
        assert editor.textCursor().selectionStart() == 3

    def test_multiline_selection_is_duplicated(self, editor):
        editor.setPlainText("a\nb\nc")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)  # "a\nb"
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        assert editor.toPlainText() == "a\nba\nb\nc"

    def test_selection_duplicate_is_single_undo(self, editor):
        editor.setPlainText("abcdef")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(3, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        editor.undo()
        assert editor.toPlainText() == "abcdef"

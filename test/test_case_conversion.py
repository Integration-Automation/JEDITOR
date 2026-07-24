"""Tests for selection case conversion in the editor."""
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


def _select(editor, start: int, end: int) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestUppercase:
    def test_uppercases_selection(self, editor):
        editor.setPlainText("hello world")
        _select(editor, 0, 5)
        editor.uppercase_selection()
        assert editor.toPlainText() == "HELLO world"

    def test_selection_is_kept(self, editor):
        editor.setPlainText("hello")
        _select(editor, 0, 5)
        editor.uppercase_selection()
        assert editor.textCursor().selectedText() == "HELLO"

    def test_no_selection_is_noop(self, editor):
        editor.setPlainText("hello")
        cursor = editor.textCursor()
        cursor.setPosition(2)
        editor.setTextCursor(cursor)
        editor.uppercase_selection()
        assert editor.toPlainText() == "hello"


class TestLowercase:
    def test_lowercases_selection(self, editor):
        editor.setPlainText("HELLO WORLD")
        _select(editor, 6, 11)
        editor.lowercase_selection()
        assert editor.toPlainText() == "HELLO world"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("HELLO")
        _select(editor, 0, 5)
        editor.lowercase_selection()
        editor.undo()
        assert editor.toPlainText() == "HELLO"


class TestMultilineCase:
    def test_uppercase_spans_lines(self, editor):
        editor.setPlainText("aaa\nbbb")
        _select(editor, 0, 7)
        editor.uppercase_selection()
        assert editor.toPlainText() == "AAA\nBBB"

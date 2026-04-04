"""Tests for CodeEditor widget functionality."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def app():
    """Ensure QApplication exists."""
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@pytest.fixture()
def editor(app):
    """Create a CodeEditor instance with a mocked parent."""
    # Patch Jedi environment check to avoid venv lookup
    with patch("je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check") as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        mock_parent = MagicMock()
        mock_parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        ed = CodeEditor(mock_parent)
    yield ed
    ed.close()
    ed.deleteLater()


class TestCodeEditorBasic:
    def test_initial_state(self, editor):
        assert editor.toPlainText() == ""
        assert editor.blockCount() == 1

    def test_set_text(self, editor):
        editor.setPlainText("hello\nworld")
        assert editor.blockCount() == 2
        assert "hello" in editor.toPlainText()


class TestDuplicateLine:
    def test_duplicate_line(self, editor):
        editor.setPlainText("line1\nline2\nline3")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        editor.duplicate_line()
        lines = editor.toPlainText().split("\n")
        assert lines[0] == "line1"
        assert lines[1] == "line1"
        assert len(lines) == 4


class TestToggleComment:
    def test_add_comment(self, editor):
        editor.setPlainText("print('hello')")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        editor.toggle_comment()
        assert editor.toPlainText().startswith("# ")

    def test_remove_comment(self, editor):
        editor.setPlainText("# print('hello')")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        editor.toggle_comment()
        assert not editor.toPlainText().startswith("#")


class TestMoveLine:
    def test_move_line_down(self, editor):
        editor.setPlainText("AAA\nBBB\nCCC")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        editor.move_line(1)
        lines = editor.toPlainText().split("\n")
        assert lines[0] == "BBB"
        assert lines[1] == "AAA"

    def test_move_line_up_at_top_does_nothing(self, editor):
        editor.setPlainText("AAA\nBBB")
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        editor.move_line(-1)
        lines = editor.toPlainText().split("\n")
        assert lines[0] == "AAA"


class TestBracketMatching:
    def test_find_matching_bracket_parens(self, editor):
        editor.setPlainText("(hello)")
        result = editor._find_matching_bracket("(hello)", 0, "(")
        assert result == 6

    def test_find_matching_bracket_nested(self, editor):
        editor.setPlainText("((a))")
        result = editor._find_matching_bracket("((a))", 0, "(")
        assert result == 4

    def test_find_matching_bracket_no_match(self, editor):
        editor.setPlainText("(hello")
        result = editor._find_matching_bracket("(hello", 0, "(")
        assert result is None

    def test_find_matching_bracket_square(self, editor):
        text = "[1, [2], 3]"
        result = editor._find_matching_bracket(text, 0, "[")
        assert result == len(text) - 1

    def test_find_matching_bracket_curly(self, editor):
        text = "{a: {b}}"
        result = editor._find_matching_bracket(text, 0, "{")
        assert result == 7


class TestZoom:
    def test_zoom_in(self, editor):
        original_size = editor.font().pointSize()
        editor._zoom_in()
        assert editor.font().pointSize() == original_size + 1

    def test_zoom_out(self, editor):
        editor._zoom_in()
        editor._zoom_in()
        size_before = editor.font().pointSize()
        editor._zoom_out()
        assert editor.font().pointSize() == size_before - 1

    def test_zoom_in_max(self, editor):
        font = editor.font()
        font.setPointSize(72)
        editor.setFont(font)
        editor._zoom_in()
        assert editor.font().pointSize() == 72  # should not exceed

    def test_zoom_out_min(self, editor):
        font = editor.font()
        font.setPointSize(6)
        editor.setFont(font)
        editor._zoom_out()
        assert editor.font().pointSize() == 6  # should not go below

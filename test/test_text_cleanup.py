"""Tests for whitespace cleanup transforms and the editor trim command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.utils.text_cleanup.text_cleanup import (
    ensure_final_newline,
    strip_trailing_blank_lines,
    trim_trailing_whitespace,
)


class TestTrimTrailingWhitespace:
    def test_removes_trailing_spaces(self):
        assert trim_trailing_whitespace("a = 1   \nb = 2") == "a = 1\nb = 2"

    def test_removes_trailing_tabs(self):
        assert trim_trailing_whitespace("x\t\t\ny") == "x\ny"

    def test_preserves_leading_indentation(self):
        assert trim_trailing_whitespace("    x = 1  ") == "    x = 1"

    def test_blank_whitespace_line_becomes_empty(self):
        assert trim_trailing_whitespace("a\n   \nb") == "a\n\nb"

    def test_line_count_is_preserved(self):
        text = "a  \nb  \nc  "
        assert trim_trailing_whitespace(text).count("\n") == text.count("\n")

    def test_no_change_returns_equal_text(self):
        assert trim_trailing_whitespace("clean\ntext") == "clean\ntext"

    def test_empty_text(self):
        assert trim_trailing_whitespace("") == ""


class TestEnsureFinalNewline:
    def test_adds_newline_when_missing(self):
        assert ensure_final_newline("abc") == "abc\n"

    def test_keeps_existing_newline(self):
        assert ensure_final_newline("abc\n") == "abc\n"

    def test_empty_stays_empty(self):
        assert ensure_final_newline("") == ""


class TestStripTrailingBlankLines:
    def test_removes_trailing_blank_lines(self):
        assert strip_trailing_blank_lines("a\nb\n\n\n") == "a\nb"

    def test_keeps_internal_blank_lines(self):
        assert strip_trailing_blank_lines("a\n\nb\n\n") == "a\n\nb"

    def test_single_line_kept(self):
        assert strip_trailing_blank_lines("only") == "only"

    def test_all_blank_keeps_one_line(self):
        assert strip_trailing_blank_lines("\n\n\n") == ""


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


class TestEditorTrimCommand:
    def test_trims_document(self, editor):
        editor.setPlainText("a = 1   \nb = 2\t\n")
        assert editor.trim_trailing_whitespace_document() is True
        assert editor.toPlainText() == "a = 1\nb = 2\n"

    def test_no_change_returns_false(self, editor):
        editor.setPlainText("clean\ntext")
        assert editor.trim_trailing_whitespace_document() is False

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("a = 1   \nb = 2   ")
        editor.trim_trailing_whitespace_document()
        editor.undo()
        assert editor.toPlainText() == "a = 1   \nb = 2   "

    def test_caret_line_is_preserved(self, editor):
        editor.setPlainText("aaa   \nbbb   \nccc")
        cursor = editor.textCursor()
        cursor.setPosition(editor.document().findBlockByNumber(1).position() + 2)
        editor.setTextCursor(cursor)
        editor.trim_trailing_whitespace_document()
        assert editor.textCursor().blockNumber() == 1

    def test_caret_column_is_clamped(self, editor):
        editor.setPlainText("aaa      ")  # caret out in the trailing spaces
        cursor = editor.textCursor()
        cursor.setPosition(8)  # inside the trailing whitespace
        editor.setTextCursor(cursor)
        editor.trim_trailing_whitespace_document()
        # After trimming, the line is "aaa" (len 3); the caret clamps to <= 3.
        assert editor.textCursor().positionInBlock() <= 3

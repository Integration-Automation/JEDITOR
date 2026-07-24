"""Tests for occurrence highlighting wired into the code editor."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
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


class TestOccurrenceHighlight:
    def test_multiple_occurrences_reported(self, editor):
        text = "value = value + 1"
        editor.setPlainText(text)
        # caret on the first 'value'
        assert editor.word_occurrences_under_cursor(text, 0) == [0, 8]

    def test_single_occurrence_not_highlighted(self, editor):
        text = "unique = 1"
        editor.setPlainText(text)
        assert editor.word_occurrences_under_cursor(text, 0) == []

    def test_whitespace_position_returns_empty(self, editor):
        text = "value    value"  # four spaces; position 7 has a space on both sides
        editor.setPlainText(text)
        assert editor.word_occurrences_under_cursor(text, 7) == []

    def test_keyword_not_highlighted(self, editor):
        text = "def a(): pass\ndef b(): pass"
        editor.setPlainText(text)
        assert editor.word_occurrences_under_cursor(text, 0) == []  # 'def'

    def test_large_document_is_skipped(self, editor):
        from je_editor.pyside_ui.code.plaintext_code_edit import code_edit_plaintext
        big = "value = value\n" + ("x = 1\n" * code_edit_plaintext._OCCURRENCE_MAX_CHARS)
        assert editor.word_occurrences_under_cursor(big, 0) == []

    def test_cursor_move_sets_extra_selections(self, editor):
        editor.setPlainText("total = total + total")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor._highlight_matching_bracket()  # the cursorPositionChanged handler
        # current-line selection + three occurrence selections
        assert len(editor.extraSelections()) >= 3

    def test_no_highlight_for_unique_word_selection(self, editor):
        editor.setPlainText("alpha = beta")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor._highlight_matching_bracket()
        # only the current-line highlight, no occurrence highlights
        assert len(editor.extraSelections()) == 1

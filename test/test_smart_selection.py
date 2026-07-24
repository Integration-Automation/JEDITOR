"""Tests for smart selection expansion logic and its editor manager."""
from __future__ import annotations

import textwrap
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.selection.smart_selection import candidate_ranges, expand_selection


class TestCandidateRanges:
    def test_word_is_the_smallest_candidate(self):
        text = "value = 1"
        first = candidate_ranges(text, 0)[0]
        assert text[first[0]:first[1]] == "value"

    def test_whole_document_is_the_largest(self):
        text = "value = 1"
        assert candidate_ranges(text, 0)[-1] == (0, len(text))

    def test_empty_text(self):
        assert candidate_ranges("", 0) == [(0, 0)]

    def test_line_candidate_present(self):
        text = "a = 1\nb = 2"
        ranges = candidate_ranges(text, 0)
        assert (0, 5) in ranges  # first line "a = 1"


class TestExpandSelection:
    def test_caret_expands_to_word(self):
        text = "value = 1"
        assert expand_selection(text, 0, 0) == (0, 5)

    def test_word_expands_to_line(self):
        text = "value = 1\nother = 2"
        # start with the word "value" selected -> expands to the whole first line
        assert expand_selection(text, 0, 5) == (0, 9)

    def test_line_expands_to_block(self):
        text = textwrap.dedent("""\
            def run():
                x = 1
                y = 2""")
        # line 1 ("    x = 1") is offsets 11..20; expanding reaches the function block
        line_start = text.index("    x = 1")
        line_end = line_start + len("    x = 1")
        expanded = expand_selection(text, line_start, line_end)
        assert expanded == (0, len(text))

    def test_expands_to_whole_document_eventually(self):
        text = "a = 1\nb = 2"
        # selecting the first line expands to the whole document
        assert expand_selection(text, 0, 5) == (0, len(text))

    def test_whole_document_cannot_expand(self):
        text = "a = 1"
        assert expand_selection(text, 0, len(text)) is None

    def test_non_word_position_expands_to_line(self):
        text = "a + b"
        # caret on the '+' (position 2) has no word, so expand to the line
        assert expand_selection(text, 2, 2) == (0, 5)


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


def _place_caret(editor, position: int) -> None:
    cursor = editor.textCursor()
    cursor.setPosition(position)
    editor.setTextCursor(cursor)


def _selected_text(editor) -> str:
    return editor.textCursor().selectedText()


class TestSmartSelectionManager:
    def test_expand_selects_word(self, editor):
        editor.setPlainText("value = 1")
        _place_caret(editor, 0)
        editor.expand_selection()
        assert _selected_text(editor) == "value"

    def test_expand_twice_grows(self, editor):
        editor.setPlainText("value = 1")
        _place_caret(editor, 0)
        editor.expand_selection()
        first = editor.textCursor().selectionEnd() - editor.textCursor().selectionStart()
        editor.expand_selection()
        second = editor.textCursor().selectionEnd() - editor.textCursor().selectionStart()
        assert second > first

    def test_shrink_returns_to_previous(self, editor):
        editor.setPlainText("value = 1")
        _place_caret(editor, 0)
        editor.expand_selection()  # word
        editor.expand_selection()  # line
        editor.shrink_selection()  # back to word
        assert _selected_text(editor) == "value"

    def test_shrink_without_history_is_noop(self, editor):
        editor.setPlainText("value = 1")
        _place_caret(editor, 0)
        assert editor.smart_selection_manager.shrink() is False

    def test_manual_selection_change_resets_stack(self, editor):
        editor.setPlainText("value = other")
        _place_caret(editor, 0)
        editor.expand_selection()  # selects "value"
        # user manually selects something else
        cursor = editor.textCursor()
        cursor.setPosition(8)
        cursor.setPosition(13, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        # shrink should now be a no-op because the stack was invalidated
        assert editor.smart_selection_manager.shrink() is False

    def test_expand_at_document_end_stops(self, editor):
        editor.setPlainText("ab")
        cursor = editor.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(2, QTextCursor.MoveMode.KeepAnchor)
        editor.setTextCursor(cursor)
        # whole document already selected -> expand returns False
        assert editor.smart_selection_manager.expand() is False

"""Tests for the Qt bookmark manager against a real editor document."""
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


def _place_cursor(editor, line: int) -> None:
    block = editor.document().findBlockByNumber(line)
    cursor = editor.textCursor()
    cursor.setPosition(block.position())
    editor.setTextCursor(cursor)


class TestBookmarkManager:
    """Toggling, listing and navigation."""

    def test_toggle_adds_a_bookmark(self, editor):
        editor.setPlainText("a\nb\nc\nd")
        assert editor.bookmark_manager.toggle(1) is True
        assert editor.bookmark_manager.bookmarked_lines() == [1]

    def test_toggle_twice_removes_it(self, editor):
        editor.setPlainText("a\nb\nc\nd")
        editor.bookmark_manager.toggle(1)
        assert editor.bookmark_manager.toggle(1) is False
        assert editor.bookmark_manager.bookmarked_lines() == []

    def test_is_bookmarked(self, editor):
        editor.setPlainText("a\nb\nc")
        editor.bookmark_manager.toggle(2)
        assert editor.bookmark_manager.is_bookmarked(2)
        assert not editor.bookmark_manager.is_bookmarked(0)

    def test_toggle_current_uses_caret_line(self, editor):
        editor.setPlainText("a\nb\nc\nd")
        _place_cursor(editor, 2)
        editor.bookmark_manager.toggle_current()
        assert editor.bookmark_manager.bookmarked_lines() == [2]

    def test_clear_removes_all(self, editor):
        editor.setPlainText("a\nb\nc")
        editor.bookmark_manager.toggle(0)
        editor.bookmark_manager.toggle(2)
        editor.bookmark_manager.clear()
        assert editor.bookmark_manager.bookmarked_lines() == []

    def test_bookmark_follows_text_inserted_above(self, editor):
        # A QTextCursor anchor moves down when lines are added above it.
        editor.setPlainText("a\nb\nc\nd")
        editor.bookmark_manager.toggle(2)  # bookmark on "c"
        # Insert two new lines at the very top.
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.insertText("x\ny\n")
        # "c" is now on line 4; the bookmark should have followed it.
        assert editor.bookmark_manager.bookmarked_lines() == [4]

    def test_go_to_next_moves_caret(self, editor):
        editor.setPlainText("a\nb\nc\nd\ne")
        editor.bookmark_manager.toggle(1)
        editor.bookmark_manager.toggle(3)
        _place_cursor(editor, 0)
        assert editor.bookmark_manager.go_to_next() == 1
        assert editor.textCursor().blockNumber() == 1

    def test_go_to_next_wraps(self, editor):
        editor.setPlainText("a\nb\nc\nd")
        editor.bookmark_manager.toggle(1)
        _place_cursor(editor, 3)
        assert editor.bookmark_manager.go_to_next() == 1

    def test_go_to_previous_moves_caret(self, editor):
        editor.setPlainText("a\nb\nc\nd\ne")
        editor.bookmark_manager.toggle(1)
        editor.bookmark_manager.toggle(3)
        _place_cursor(editor, 4)
        assert editor.bookmark_manager.go_to_previous() == 3

    def test_navigation_without_bookmarks_returns_none(self, editor):
        editor.setPlainText("a\nb\nc")
        assert editor.bookmark_manager.go_to_next() is None
        assert editor.bookmark_manager.go_to_previous() is None

    def test_toggle_out_of_range_line_is_safe(self, editor):
        editor.setPlainText("a\nb")
        assert editor.bookmark_manager.toggle(99) is False
        assert editor.bookmark_manager.bookmarked_lines() == []

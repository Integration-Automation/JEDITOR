"""Tests for CodeEditor cursor-jump history recording and back/forward."""
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


def _goto(editor, line: int) -> None:
    block = editor.document().findBlockByNumber(line)
    cursor = editor.textCursor()
    cursor.setPosition(block.position())
    editor.setTextCursor(cursor)


class TestNavigationHistory:
    def test_small_moves_are_not_recorded(self, editor):
        editor.setPlainText("\n".join(f"line {i}" for i in range(30)))
        _goto(editor, 0)
        _goto(editor, 2)  # only 2 lines -> below the jump threshold
        # Only the seeded starting point should be present.
        assert editor.location_history.entries in ([0], [2], [])

    def test_large_jump_is_recorded(self, editor):
        editor.setPlainText("\n".join(f"line {i}" for i in range(30)))
        _goto(editor, 0)
        _goto(editor, 20)  # a big jump
        assert 20 in editor.location_history.entries

    def test_back_returns_to_previous_location(self, editor):
        editor.setPlainText("\n".join(f"line {i}" for i in range(30)))
        _goto(editor, 1)
        _goto(editor, 25)  # jump forward
        assert editor.navigate_back() is True
        assert editor.textCursor().blockNumber() == 1

    def test_forward_after_back(self, editor):
        editor.setPlainText("\n".join(f"line {i}" for i in range(30)))
        _goto(editor, 1)
        _goto(editor, 25)
        editor.navigate_back()
        assert editor.navigate_forward() is True
        assert editor.textCursor().blockNumber() == 25

    def test_navigation_does_not_pollute_history(self, editor):
        editor.setPlainText("\n".join(f"line {i}" for i in range(30)))
        _goto(editor, 1)
        _goto(editor, 25)
        before = editor.location_history.entries
        editor.navigate_back()
        editor.navigate_forward()
        # Back/forward must not append new entries.
        assert editor.location_history.entries == before

    def test_back_with_no_history_returns_false(self, editor):
        editor.setPlainText("a\nb\nc")
        assert editor.navigate_back() is False

    def test_forward_with_no_history_returns_false(self, editor):
        editor.setPlainText("a\nb\nc")
        assert editor.navigate_forward() is False

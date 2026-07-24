"""Tests for CodeEditor folding/bookmark wiring: shortcuts, gutter, caching."""
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


FUNCTION_SOURCE = "def run():\n    x = 1\n    y = 2\nz = 3"


def _place_cursor(editor, line: int) -> None:
    block = editor.document().findBlockByNumber(line)
    cursor = editor.textCursor()
    cursor.setPosition(block.position())
    editor.setTextCursor(cursor)


class TestEditorFoldBookmarkWiring:
    """The editor exposes managers and reacts to edits and clicks."""

    def test_managers_are_attached(self, editor):
        assert editor.folding_manager is not None
        assert editor.bookmark_manager is not None

    def test_gutter_is_wider_than_numbers_alone(self, editor):
        editor.setPlainText("a\nb")
        # Gutter must leave room for the bookmark and fold columns (28px total).
        assert editor.line_number_width() >= 12 + 28

    def test_toggle_fold_at_cursor(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        _place_cursor(editor, 0)
        editor.toggle_fold_at_cursor()
        assert editor.folding_manager.is_folded(0)

    def test_fold_all_and_unfold_all(self, editor):
        editor.setPlainText("def a():\n    x = 1\ndef b():\n    y = 2")
        editor.fold_all()
        assert editor.folding_manager.is_any_folded()
        editor.unfold_all()
        assert not editor.folding_manager.is_any_folded()

    def test_toggle_bookmark_shortcut_method(self, editor):
        editor.setPlainText("a\nb\nc")
        _place_cursor(editor, 1)
        editor.toggle_bookmark()
        assert editor.bookmark_manager.bookmarked_lines() == [1]

    def test_next_previous_bookmark_methods(self, editor):
        editor.setPlainText("a\nb\nc\nd\ne")
        editor.bookmark_manager.toggle(1)
        editor.bookmark_manager.toggle(3)
        _place_cursor(editor, 0)
        editor.next_bookmark()
        assert editor.textCursor().blockNumber() == 1
        editor.previous_bookmark()
        # wraps back to line 3 (the last bookmark before line 1)
        assert editor.textCursor().blockNumber() == 3

    def test_fold_header_cache_is_invalidated_on_edit(self, editor):
        editor.setPlainText("a = 1\nb = 2")
        assert editor._foldable_header_lines() == set()
        editor.setPlainText(FUNCTION_SOURCE)
        # After the edit the cache must recompute and see the new header.
        assert 0 in editor._foldable_header_lines()

    def test_folds_self_heal_after_edit(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        _place_cursor(editor, 0)
        editor.toggle_fold_at_cursor()
        # Editing to remove the header should reveal the previously hidden body.
        editor.setPlainText("a = 1\nb = 2\nc = 3")
        assert all(
            editor.document().findBlockByNumber(line).isVisible()
            for line in range(3)
        )

    @staticmethod
    def _first_line_y(editor) -> int:
        """The vertical centre of the first visible line (past the doc margin)."""
        block = editor.firstVisibleBlock()
        geo = editor.blockBoundingGeometry(block).translated(editor.contentOffset())
        return int(geo.top() + geo.height() / 2)

    def test_gutter_click_on_fold_column_toggles_fold(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        # Force a layout pass so block geometry is available.
        editor.resize(400, 300)
        # x in the fold column (far right of the gutter), y on the first line.
        fold_x = editor.line_number.width() - 2
        editor.handle_gutter_click(fold_x, self._first_line_y(editor))
        # The first visible line is line 0, the foldable header.
        assert editor.folding_manager.is_folded(0)

    def test_gutter_click_on_bookmark_column_toggles_bookmark(self, editor):
        editor.setPlainText("a\nb\nc")
        editor.resize(400, 300)
        editor.handle_gutter_click(2, self._first_line_y(editor))  # x in bookmark column
        assert editor.bookmark_manager.bookmarked_lines() == [0]

    def test_gutter_click_outside_any_line_is_safe(self, editor):
        editor.setPlainText("a\nb")
        editor.resize(400, 300)
        editor.handle_gutter_click(2, 99999)  # far below any line

    def test_gutter_line_at_y_out_of_range(self, editor):
        editor.setPlainText("a\nb")
        editor.resize(400, 300)
        assert editor.gutter_line_at_y(99999) == -1

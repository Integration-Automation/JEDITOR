"""Tests for the Qt folding manager against a real editor document."""
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


def _block_visible(editor, line: int) -> bool:
    return editor.document().findBlockByNumber(line).isVisible()


# A function spanning lines 0..2, then a flat line 3.
FUNCTION_SOURCE = "def run():\n    x = 1\n    y = 2\nz = 3"


class TestFoldingManager:
    """Folding toggles block visibility without touching text."""

    def test_foldable_header_is_detected(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        assert 0 in editor.folding_manager.foldable_header_lines()

    def test_fold_hides_body_blocks(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        editor.folding_manager.toggle_fold(0)
        assert _block_visible(editor, 0)          # header stays visible
        assert not _block_visible(editor, 1)      # body hidden
        assert not _block_visible(editor, 2)
        assert _block_visible(editor, 3)          # sibling stays visible

    def test_fold_does_not_change_text(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        editor.folding_manager.toggle_fold(0)
        assert editor.toPlainText() == FUNCTION_SOURCE

    def test_unfold_restores_visibility(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        editor.folding_manager.toggle_fold(0)
        editor.folding_manager.toggle_fold(0)
        assert all(_block_visible(editor, line) for line in range(4))

    def test_toggle_on_non_header_is_ignored(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        assert editor.folding_manager.toggle_fold(3) is False

    def test_is_folded_reflects_state(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        assert not editor.folding_manager.is_folded(0)
        editor.folding_manager.toggle_fold(0)
        assert editor.folding_manager.is_folded(0)

    def test_fold_all_folds_every_region(self, editor):
        editor.setPlainText("def a():\n    x = 1\ndef b():\n    y = 2")
        editor.folding_manager.fold_all()
        assert not _block_visible(editor, 1)
        assert not _block_visible(editor, 3)

    def test_unfold_all_shows_everything(self, editor):
        editor.setPlainText("def a():\n    x = 1\ndef b():\n    y = 2")
        editor.folding_manager.fold_all()
        editor.folding_manager.unfold_all()
        assert all(_block_visible(editor, line) for line in range(4))

    def test_refresh_drops_stale_fold(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        editor.folding_manager.toggle_fold(0)
        # Replace with text where line 0 is no longer a header.
        editor.setPlainText("x = 1\ny = 2\nz = 3")
        editor.folding_manager.refresh()
        assert all(_block_visible(editor, line) for line in range(3))
        assert not editor.folding_manager.is_any_folded()

    def test_refresh_is_self_healing(self, editor):
        # Even if a block was left hidden, refresh with no valid fold reveals it.
        editor.setPlainText(FUNCTION_SOURCE)
        editor.document().findBlockByNumber(2).setVisible(False)
        editor.folding_manager.refresh()
        assert _block_visible(editor, 2)

    def test_folded_header_lines_reports_state(self, editor):
        editor.setPlainText(FUNCTION_SOURCE)
        editor.folding_manager.toggle_fold(0)
        assert editor.folding_manager.folded_header_lines() == {0}

    def test_editing_unfolded_document_costs_nothing_extra(self, editor):
        # With nothing folded, a text change must not re-hide anything.
        editor.setPlainText(FUNCTION_SOURCE)
        editor.insertPlainText("\n# trailing")
        assert all(
            _block_visible(editor, line)
            for line in range(editor.document().blockCount())
        )

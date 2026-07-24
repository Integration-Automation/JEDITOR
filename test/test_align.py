"""Tests for delimiter alignment and its editor command."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.utils.align.align import align_by_delimiter


class TestAlignByDelimiter:
    def test_aligns_equals(self):
        lines = ["a = 1", "bbb = 2", "cc = 3"]
        result = align_by_delimiter(lines, "=")
        # All '=' land in the same column.
        columns = {line.index("=") for line in result}
        assert len(columns) == 1

    def test_preserves_values(self):
        result = align_by_delimiter(["x=1", "yy=2"], "=")
        assert result[0].endswith("1")
        assert result[1].endswith("2")

    def test_single_space_around_delimiter(self):
        result = align_by_delimiter(["x=1"], "=")
        assert result[0] == "x = 1"

    def test_lines_without_delimiter_unchanged(self):
        result = align_by_delimiter(["a = 1", "# comment", "bb = 2"], "=")
        assert result[1] == "# comment"

    def test_no_delimiter_anywhere_returns_copy(self):
        original = ["a", "b"]
        result = align_by_delimiter(original, "=")
        assert result == ["a", "b"]

    def test_empty_delimiter_returns_copy(self):
        assert align_by_delimiter(["a=1"], "") == ["a=1"]

    def test_colon_delimiter(self):
        result = align_by_delimiter(["a: 1", "bbb: 2"], ":")
        columns = {line.index(":") for line in result}
        assert len(columns) == 1

    def test_only_first_occurrence_aligned(self):
        # A second '=' in the value must not be treated as the alignment point.
        result = align_by_delimiter(["a = b = c"], "=")
        assert result[0] == "a = b = c"


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


def _select_lines(editor, start_line: int, end_line: int) -> None:
    document = editor.document()
    cursor = editor.textCursor()
    cursor.setPosition(document.findBlockByNumber(start_line).position())
    end_block = document.findBlockByNumber(end_line)
    cursor.setPosition(
        end_block.position() + end_block.length() - 1, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)


class TestEditorAlign:
    @staticmethod
    def _patch_dialog(delimiter, accepted=True):
        return patch(
            "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.QInputDialog.getText",
            return_value=(delimiter, accepted),
        )

    def test_align_selected_lines(self, editor):
        editor.setPlainText("a = 1\nbbb = 2")
        _select_lines(editor, 0, 1)
        with self._patch_dialog("="):
            editor.align_selected_lines()
        lines = editor.toPlainText().split("\n")
        assert lines[0].index("=") == lines[1].index("=")

    def test_cancel_is_noop(self, editor):
        editor.setPlainText("a = 1\nbbb = 2")
        _select_lines(editor, 0, 1)
        with self._patch_dialog("=", accepted=False):
            editor.align_selected_lines()
        assert editor.toPlainText() == "a = 1\nbbb = 2"

    def test_is_single_undo_step(self, editor):
        editor.setPlainText("a=1\nbbb=2")
        _select_lines(editor, 0, 1)
        with self._patch_dialog("="):
            editor.align_selected_lines()
        editor.undo()
        assert editor.toPlainText() == "a=1\nbbb=2"

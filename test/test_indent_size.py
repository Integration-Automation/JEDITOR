"""Tests that tab-indent, unindent and Enter auto-indent honour indent_size."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict


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


@pytest.fixture()
def restore_indent_size():
    original = user_setting_dict.get("indent_size", 4)
    yield
    user_setting_dict["indent_size"] = original


def _select_all(editor) -> None:
    cursor = editor.textCursor()
    cursor.select(QTextCursor.SelectionType.Document)
    editor.setTextCursor(cursor)


class TestIndentSize:
    def test_defaults_to_four(self, editor, restore_indent_size):
        user_setting_dict.pop("indent_size", None)
        assert editor.indent_size() == 4

    def test_reads_the_setting(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 2
        assert editor.indent_size() == 2

    def test_clamps_invalid_value(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 0
        assert editor.indent_size() == 4
        user_setting_dict["indent_size"] = 999
        assert editor.indent_size() == 16


class TestIndentSelectionHonoursSetting:
    def test_indent_uses_two_spaces(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 2
        editor.setPlainText("a\nb")
        _select_all(editor)
        editor._indent_selection(indent=True)
        assert editor.toPlainText() == "  a\n  b"

    def test_indent_uses_four_spaces(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 4
        editor.setPlainText("a")
        _select_all(editor)
        editor._indent_selection(indent=True)
        assert editor.toPlainText() == "    a"

    def test_unindent_removes_one_unit(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 2
        editor.setPlainText("    a")  # 4 spaces
        _select_all(editor)
        editor._indent_selection(indent=False)
        assert editor.toPlainText() == "  a"  # removed 2

    def test_indent_is_single_undo_step(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 4
        editor.setPlainText("a\nb")
        _select_all(editor)
        editor._indent_selection(indent=True)
        editor.undo()
        assert editor.toPlainText() == "a\nb"

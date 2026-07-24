"""Tests for indent-width detection and its per-editor application."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.indentation.indent_convert import detect_indent_width


class TestDetectIndentWidth:
    def test_four_space_indentation(self):
        text = "def f():\n    x = 1\n    if x:\n        y = 2"
        assert detect_indent_width(text) == 4

    def test_two_space_indentation(self):
        text = "def f():\n  x = 1\n  if x:\n    y = 2"
        assert detect_indent_width(text) == 2

    def test_no_indentation_returns_none(self):
        assert detect_indent_width("a = 1\nb = 2") is None

    def test_tab_indented_returns_none(self):
        # Tabs have no leading spaces, so space-width detection finds nothing.
        assert detect_indent_width("def f():\n\tx = 1") is None

    def test_most_common_step_wins(self):
        # Mostly 2-space steps with one noisy line.
        text = "a\n  b\n    c\n  d\n    e\n      f"
        assert detect_indent_width(text) == 2

    def test_single_indented_block(self):
        assert detect_indent_width("class A:\n    pass") == 4

    def test_empty_text(self):
        assert detect_indent_width("") is None


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


class TestApplyDetectedIndentation:
    def test_detects_two_space_override(self, editor):
        editor.setPlainText("def f():\n  x = 1\n  y = 2")
        assert editor.apply_detected_indentation() == 2
        assert editor.indent_size() == 2

    def test_override_beats_global_setting(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 8
        editor.setPlainText("def f():\n  x = 1")
        editor.apply_detected_indentation()
        # per-file override (2) wins over the global setting (8)
        assert editor.indent_size() == 2

    def test_tab_file_clears_override(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 4
        editor.setPlainText("def f():\n  x = 1")
        editor.apply_detected_indentation()          # sets override to 2
        editor.setPlainText("def f():\n\tx = 1")     # now tab-indented
        assert editor.apply_detected_indentation() is None
        assert editor.indent_size() == 4             # back to global

    def test_no_indentation_uses_global(self, editor, restore_indent_size):
        user_setting_dict["indent_size"] = 4
        editor.setPlainText("a = 1\nb = 2")
        assert editor.apply_detected_indentation() is None
        assert editor.indent_size() == 4

    def test_detected_indent_drives_tab_key(self, editor):
        from PySide6.QtGui import QTextCursor
        editor.setPlainText("def f():\n  x = 1")   # 2-space file
        editor.apply_detected_indentation()
        editor.setPlainText("a")
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        editor.setTextCursor(cursor)
        editor._indent_selection(indent=True)
        assert editor.toPlainText() == "  a"        # indents by the detected 2 spaces

"""Tests for yapf formatting and applying it on save."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.main_ui.menu.file_menu.encoding_actions import format_before_save
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.format_code.yapf_format import format_python_source

BADLY_SPACED = "x   =   1\ny=2\n"


class TestFormatPythonSource:
    def test_reformats_spacing(self):
        formatted = format_python_source(BADLY_SPACED)
        assert "x = 1" in formatted

    def test_already_formatted_source_is_unchanged(self):
        source = "x = 1\ny = 2\n"
        assert format_python_source(source) == source

    def test_syntax_error_is_returned_untouched(self):
        # Half-written code must not break a save.
        broken = "def broken(:\n    pass\n"
        assert format_python_source(broken) == broken

    def test_empty_source(self):
        assert format_python_source("") == ""
        assert format_python_source("   \n") == "   \n"


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def widget(app, tmp_path):
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from PySide6.QtWidgets import QPlainTextEdit
    tab = MagicMock(spec=EditorWidget)
    tab.code_edit = QPlainTextEdit()
    tab.code_edit.jump_to_line = MagicMock()
    tab.current_file = str(tmp_path / "sample.py")
    yield tab
    tab.code_edit.deleteLater()


@pytest.fixture(autouse=True)
def restore_setting():
    original = user_setting_dict.get("format_on_save", False)
    yield
    user_setting_dict["format_on_save"] = original


class TestFormatBeforeSave:
    def test_does_nothing_while_the_setting_is_off(self, widget):
        user_setting_dict["format_on_save"] = False
        widget.code_edit.setPlainText(BADLY_SPACED)
        assert format_before_save(widget) is False
        assert widget.code_edit.toPlainText() == BADLY_SPACED

    def test_formats_when_the_setting_is_on(self, widget):
        user_setting_dict["format_on_save"] = True
        widget.code_edit.setPlainText(BADLY_SPACED)
        assert format_before_save(widget) is True
        assert "x = 1" in widget.code_edit.toPlainText()

    def test_only_python_files_are_formatted(self, widget, tmp_path):
        user_setting_dict["format_on_save"] = True
        widget.current_file = str(tmp_path / "notes.txt")
        widget.code_edit.setPlainText(BADLY_SPACED)
        assert format_before_save(widget) is False

    def test_a_file_that_was_never_saved_is_skipped(self, widget):
        user_setting_dict["format_on_save"] = True
        widget.current_file = None
        widget.code_edit.setPlainText(BADLY_SPACED)
        assert format_before_save(widget) is False

    def test_already_formatted_text_is_left_alone(self, widget):
        user_setting_dict["format_on_save"] = True
        widget.code_edit.setPlainText("x = 1\n")
        assert format_before_save(widget) is False

    def test_broken_code_still_saves(self, widget):
        user_setting_dict["format_on_save"] = True
        broken = "def broken(:\n    pass\n"
        widget.code_edit.setPlainText(broken)
        assert format_before_save(widget) is False
        assert widget.code_edit.toPlainText() == broken

    def test_the_caret_line_is_restored(self, widget):
        user_setting_dict["format_on_save"] = True
        widget.code_edit.setPlainText(BADLY_SPACED)
        cursor = widget.code_edit.textCursor()
        cursor.setPosition(widget.code_edit.document().findBlockByNumber(1).position())
        widget.code_edit.setTextCursor(cursor)
        format_before_save(widget)
        widget.code_edit.jump_to_line.assert_called_once_with(2)

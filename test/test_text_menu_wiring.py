"""Integration guard: the Text menu builds, and every command it wires exists."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QMainWindow, QMenuBar, QTabWidget

# Every code_edit method name the Text menu dispatches to via _run_on_editor,
# plus the ones wired through dedicated helpers. Keeping this list in sync is the
# point of the test: a typo in the menu wiring shows up as a missing attribute.
EXPECTED_EDITOR_METHODS = [
    "uppercase_selection",
    "lowercase_selection",
    "swapcase_selection",
    "titlecase_selection",
    "to_snake_case_selection",
    "to_camel_case_selection",
    "to_pascal_case_selection",
    "to_kebab_case_selection",
    "number_to_hex_selection",
    "number_to_decimal_selection",
    "number_to_binary_selection",
    "base64_encode_selection",
    "base64_decode_selection",
    "url_encode_selection",
    "url_decode_selection",
    "html_escape_selection",
    "html_unescape_selection",
    "json_escape_selection",
    "json_unescape_selection",
    "remove_duplicate_selected_lines",
    "reverse_selected_lines",
    "natural_sort_selected_lines",
    "remove_blank_selected_lines",
    "align_selected_lines",
    "trim_trailing_whitespace_document",
    "convert_indentation_to_spaces",
    "convert_indentation_to_tabs",
]


@pytest.fixture(scope="module")
def app():
    from PySide6.QtWidgets import QApplication
    return QApplication.instance() or QApplication([])


def _code_editor(app):
    with patch(
        "je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext.venv_check"
    ) as mock_venv:
        mock_venv.return_value = MagicMock(exists=MagicMock(return_value=False))
        parent = MagicMock()
        parent.current_file = None
        from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor
        return CodeEditor(parent)


class TestEditorHasWiredMethods:
    @pytest.mark.parametrize("method_name", EXPECTED_EDITOR_METHODS)
    def test_method_exists_and_callable(self, app, method_name):
        editor = _code_editor(app)
        try:
            assert callable(getattr(editor, method_name))
        finally:
            editor.close()
            editor.deleteLater()


class TestTextMenuBuilds:
    def test_set_text_menu_runs_without_error(self, app):
        from je_editor.pyside_ui.main_ui.menu.text_menu.build_text_menu import set_text_menu
        window = QMainWindow()
        window.menu = QMenuBar()
        window.font_database = QFontDatabase()
        window.tab_widget = QTabWidget()
        set_text_menu(window)
        assert window.text_menu is not None
        # The menu should hold several actions and submenus.
        assert len(window.text_menu.actions()) > 5
        window.deleteLater()

    def test_run_on_editor_dispatches(self, app):
        from je_editor.pyside_ui.main_ui.menu.text_menu.build_text_menu import _run_on_editor
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

        editor = _code_editor(app)
        editor.setPlainText("myVarName")
        from PySide6.QtGui import QTextCursor
        cursor = editor.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        editor.setTextCursor(cursor)

        # A spec'd mock passes isinstance(widget, EditorWidget) natively.
        widget = MagicMock(spec=EditorWidget)
        widget.code_edit = editor
        window = MagicMock()
        window.tab_widget.currentWidget.return_value = widget

        _run_on_editor(window, "to_snake_case_selection")
        assert editor.toPlainText() == "my_var_name"
        editor.close()
        editor.deleteLater()

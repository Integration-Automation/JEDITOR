from __future__ import annotations

from typing import TYPE_CHECKING

import black

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction, QKeySequence
from yapf.yapflib.yapf_api import FormatCode

from je_editor.utils.json_format.json_process import reformat_json


def set_check_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.check_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("check_code_style_menu_label"))
    # Yapf code check
    ui_we_want_to_set.check_menu.yapf_check_python_action = QAction(
        language_wrapper.language_word_dict.get("yapf_reformat_label"))
    ui_we_want_to_set.check_menu.yapf_check_python_action.setShortcut(
        QKeySequence("Ctrl+Shift+Y"))
    ui_we_want_to_set.check_menu.yapf_check_python_action.triggered.connect(
        lambda: yapf_check_python_code(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.yapf_check_python_action)
    # Black code check
    ui_we_want_to_set.check_menu.black_check_python_action = QAction(
        language_wrapper.language_word_dict.get("black_reformat_label"))
    ui_we_want_to_set.check_menu.black_check_python_action.setShortcut(
        QKeySequence("Ctrl+Shift+L"))
    ui_we_want_to_set.check_menu.black_check_python_action.triggered.connect(
        lambda: black_check_python_code(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.black_check_python_action)
    # Reformat JSON
    ui_we_want_to_set.check_menu.reformat_json_action = QAction(
        language_wrapper.language_word_dict.get("reformat_json_label"))
    ui_we_want_to_set.check_menu.reformat_json_action.setShortcut("Ctrl+j")
    ui_we_want_to_set.check_menu.reformat_json_action.triggered.connect(
        lambda: reformat_json_text(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.reformat_json_action)


def yapf_check_python_code(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()
        widget.code_result.setPlainText("")
        format_code = FormatCode(
            unformatted_source=code_text,
            verify=True,
            style_config="google"
        )
        if isinstance(format_code, tuple):
            widget.code_edit.setPlainText(format_code[0])


def black_check_python_code(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()
        widget.code_edit.setPlainText(black.format_str(code_text, mode=black.Mode()))


def reformat_json_text(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()
        widget.code_result.setPlainText("")
        widget.code_edit.setPlainText(reformat_json(code_text))

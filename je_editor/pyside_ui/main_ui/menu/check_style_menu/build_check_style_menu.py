from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction, QKeySequence
from yapf.yapflib.yapf_api import FormatCode

from je_editor.utils.json_format.json_process import reformat_json


def set_check_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.check_menu = ui_we_want_to_set.menu.addMenu("Check Code Style")
    # Yapf code check
    ui_we_want_to_set.check_menu.check_python_action = QAction("yapf")
    ui_we_want_to_set.check_menu.check_python_action.setShortcut(
        QKeySequence("Ctrl+Shift+Y"))
    ui_we_want_to_set.check_menu.check_python_action.triggered.connect(
        lambda: check_python_code(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.check_python_action)
    # Reformat JSON
    ui_we_want_to_set.check_menu.reformat_json_action = QAction("Reformat JSON")
    ui_we_want_to_set.check_menu.reformat_json_action.setShortcut("Ctrl+j")
    ui_we_want_to_set.check_menu.reformat_json_action.triggered.connect(
        lambda: reformat_json_text(
            ui_we_want_to_set
        )
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.reformat_json_action)


def check_python_code(ui_we_want_to_set: EditorMain) -> None:
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


def reformat_json_text(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()
        widget.code_result.setPlainText("")
        widget.code_edit.setPlainText(reformat_json(code_text))

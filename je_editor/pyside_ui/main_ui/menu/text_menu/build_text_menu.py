from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_user_setting.user_setting_file import user_setting_dict

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_text_menu(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.text_menu = ui_we_want_to_set.menu.addMenu("Text")
    ui_we_want_to_set.text_menu.font_menu = ui_we_want_to_set.text_menu.addMenu("Font")
    for family in ui_we_want_to_set.font_database.families():
        font_action = QAction(family, parent=ui_we_want_to_set.text_menu.font_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font(ui_we_want_to_set, action))
        ui_we_want_to_set.text_menu.font_menu.addAction(font_action)
    ui_we_want_to_set.text_menu.font_size_menu = ui_we_want_to_set.text_menu.addMenu("Font Size")
    for size in range(12, 38, 2):
        font_action = QAction(str(size), parent=ui_we_want_to_set.text_menu.font_size_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font_size(ui_we_want_to_set, action))
        ui_we_want_to_set.text_menu.font_size_menu.addAction(font_action)


def set_font(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    for code_editor in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(code_editor)
        if isinstance(widget, EditorWidget):
            widget.code_edit.setStyleSheet(
                f"font-size: {widget.code_edit.font().pointSize()}pt;"
                f"font-family: {action.text()};"
            )
            widget.code_result.setStyleSheet(
                f"font-size: {widget.code_result.font().pointSize()}pt;"
                f"font-family: {action.text()};"
            )
            user_setting_dict.update({"font": action.text()})


def set_font_size(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    for code_editor in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(code_editor)
        if type(widget) is EditorWidget:
            widget.code_edit.setStyleSheet(
                f"font-size: {int(action.text())}pt;"
                f"font-family: {widget.code_edit.font().family()};"
            )
            widget.code_result.setStyleSheet(
                f"font-size: {int(action.text())}pt;"
                f"font-family: {widget.code_result.font().family()};"
            )
            user_setting_dict.update({"font_size": int(action.text())})
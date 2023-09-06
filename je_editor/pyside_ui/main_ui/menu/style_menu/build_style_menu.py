from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.main_ui.save_user_setting.user_setting_file import user_setting_dict

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_style_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.menu.style_menu = ui_we_want_to_set.menu.addMenu("UI Style")
    for style in [
        'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml', 'dark_lightgreen.xml', 'dark_pink.xml',
        'dark_purple.xml', 'dark_red.xml', 'dark_teal.xml', 'dark_yellow.xml', 'light_amber.xml',
        'light_blue.xml', 'light_cyan.xml', 'light_cyan_500.xml', 'light_lightgreen.xml',
        'light_pink.xml', 'light_purple.xml', 'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
    ]:
        change_style_action = QAction(style, parent=ui_we_want_to_set.menu.style_menu)
        change_style_action.triggered.connect(
            lambda checked=False, action=change_style_action: set_style(ui_we_want_to_set, action))
        ui_we_want_to_set.menu.style_menu.addAction(change_style_action)


def set_style(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    ui_we_want_to_set.apply_stylesheet(ui_we_want_to_set, action.text())
    user_setting_dict.update({"ui_style": action.text()})

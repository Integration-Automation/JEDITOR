from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_menu import set_tab_menu

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtWidgets import QMenuBar

from je_editor.pyside_ui.main_ui.menu.check_style_menu.build_check_style_menu import set_check_menu
from je_editor.pyside_ui.main_ui.menu.file_menu.build_file_menu import set_file_menu
from je_editor.pyside_ui.main_ui.menu.help_menu.build_help_menu import set_help_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.build_run_menu import set_run_menu
from je_editor.pyside_ui.main_ui.menu.venv_menu.build_venv_menu import set_venv_menu


def set_menu_bar(ui_we_want_to_set: EditorMain) -> None:
    # set menu
    ui_we_want_to_set.menu = QMenuBar()
    set_file_menu(ui_we_want_to_set)
    set_run_menu(ui_we_want_to_set)
    ui_we_want_to_set.text_menu = ui_we_want_to_set.menu.addMenu("Text")
    set_check_menu(ui_we_want_to_set)
    set_help_menu(ui_we_want_to_set)
    set_venv_menu(ui_we_want_to_set)
    set_tab_menu(ui_we_want_to_set)
    ui_we_want_to_set.setMenuBar(ui_we_want_to_set.menu)

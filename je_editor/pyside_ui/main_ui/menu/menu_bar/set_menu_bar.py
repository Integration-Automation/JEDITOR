from PySide6.QtWidgets import QMainWindow, QMenuBar

from je_editor.pyside_ui.main_ui.menu.menu_bar.check_style_menu.build_check_style_menu import set_check_menu
from je_editor.pyside_ui.main_ui.menu.menu_bar.file_menu.build_file_menu import set_file_menu
from je_editor.pyside_ui.main_ui.menu.menu_bar.help_menu.build_help_menu import set_help_menu
from je_editor.pyside_ui.main_ui.menu.menu_bar.run_menu.build_run_menu import set_run_menu
from je_editor.pyside_ui.main_ui.menu.menu_bar.venv_menu.build_venv_menu import set_venv_menu


def set_menu_bar(ui_we_want_to_set: QMainWindow) -> None:
    # set menu
    ui_we_want_to_set.menu = QMenuBar()
    ui_we_want_to_set.file_menu = ui_we_want_to_set.menu.addMenu("File")
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu("Run")
    ui_we_want_to_set.text_menu = ui_we_want_to_set.menu.addMenu("Text")
    ui_we_want_to_set.check_menu = ui_we_want_to_set.menu.addMenu("Check Code Style")
    ui_we_want_to_set.help_menu = ui_we_want_to_set.menu.addMenu("Help")
    ui_we_want_to_set.venv_menu = ui_we_want_to_set.menu.addMenu("Venv")
    ui_we_want_to_set.setMenuBar(ui_we_want_to_set.menu)
    set_file_menu(ui_we_want_to_set)
    set_run_menu(ui_we_want_to_set)
    set_check_menu(ui_we_want_to_set)
    set_help_menu(ui_we_want_to_set)
    set_venv_menu(ui_we_want_to_set)

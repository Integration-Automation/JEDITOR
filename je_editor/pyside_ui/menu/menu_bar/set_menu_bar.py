from PySide6.QtWidgets import QMainWindow, QMenuBar

from je_editor.pyside_ui.menu.menu_bar.check_style_menu.build_check_style_menu import set_check_menu
from je_editor.pyside_ui.menu.menu_bar.file_menu.build_file_menu import set_file_menu
from je_editor.pyside_ui.menu.menu_bar.run_menu.build_run_menu import set_run_menu


def set_menu_bar(ui_we_want_to_set: QMainWindow):
    # set menu
    ui_we_want_to_set.menu = QMenuBar()
    ui_we_want_to_set.file_menu = ui_we_want_to_set.menu.addMenu("File")
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu("Run")
    ui_we_want_to_set.text_menu = ui_we_want_to_set.menu.addMenu("Text")
    ui_we_want_to_set.check_menu = ui_we_want_to_set.menu.addMenu("Check Code Style")
    ui_we_want_to_set.setMenuBar(ui_we_want_to_set.menu)
    set_file_menu(ui_we_want_to_set)
    set_run_menu(ui_we_want_to_set)
    set_check_menu(ui_we_want_to_set)

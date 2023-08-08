from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_ui.editor_main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction

from je_editor.pyside_ui.dialog.file_dialog.create_file_dialog import CreateFileDialog
from je_editor.pyside_ui.dialog.file_dialog.open_file_dialog import choose_file_get_open_file_path
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path


def set_file_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.file_menu.new_file_action = QAction("New File")
    ui_we_want_to_set.file_menu.new_file_action.setShortcut(
        "Ctrl+n"
    )
    ui_we_want_to_set.file_menu.new_file_action.triggered.connect(
        lambda: show_create_file_dialog(ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.new_file_action)
    ui_we_want_to_set.file_menu.open_file_action = QAction("Open File")
    ui_we_want_to_set.file_menu.open_file_action.setShortcut(
        "Ctrl+o"
    )
    ui_we_want_to_set.file_menu.open_file_action.triggered.connect(
        lambda: choose_file_get_open_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_file_action)
    ui_we_want_to_set.file_menu.save_file_action = QAction("Save File")
    ui_we_want_to_set.file_menu.save_file_action.setShortcut(
        "Ctrl+s"
    )
    ui_we_want_to_set.file_menu.save_file_action.triggered.connect(
        lambda: choose_file_get_save_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.save_file_action)


def show_create_file_dialog(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.create_file_dialog = CreateFileDialog()
    ui_we_want_to_set.create_file_dialog.show()

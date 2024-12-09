from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.encodings.python_encodings import python_encodings_list
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction, QFontDatabase

from je_editor.pyside_ui.dialog.file_dialog.create_file_dialog import CreateFileDialog
from je_editor.pyside_ui.dialog.file_dialog.open_file_dialog import choose_file_get_open_file_path, \
    choose_dir_get_dir_path
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path


def set_file_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_file_menu.py add_dock_widget "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_label"))
    ui_we_want_to_set.file_menu.new_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_new_file_label"))
    ui_we_want_to_set.file_menu.new_file_action.setShortcut(
        "Ctrl+n"
    )
    ui_we_want_to_set.file_menu.new_file_action.triggered.connect(
        lambda: show_create_file_dialog(ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.new_file_action)
    ui_we_want_to_set.file_menu.open_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_open_file_label"))
    ui_we_want_to_set.file_menu.open_file_action.setShortcut(
        "Ctrl+o"
    )
    ui_we_want_to_set.file_menu.open_file_action.triggered.connect(
        lambda: choose_file_get_open_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_file_action)
    ui_we_want_to_set.file_menu.open_folder_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_open_folder_label"))
    ui_we_want_to_set.file_menu.open_folder_action.setShortcut(
        "Ctrl+K"
    )
    ui_we_want_to_set.file_menu.open_folder_action.triggered.connect(
        lambda: choose_dir_get_dir_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_folder_action)
    ui_we_want_to_set.file_menu.save_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_save_file_label"))
    ui_we_want_to_set.file_menu.save_file_action.setShortcut(
        "Ctrl+s"
    )
    ui_we_want_to_set.file_menu.save_file_action.triggered.connect(
        lambda: choose_file_get_save_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.save_file_action)
    # Main UI font
    add_font_menu(ui_we_want_to_set)
    add_font_size_menu(ui_we_want_to_set)
    # Encoding
    add_encoding_menu(ui_we_want_to_set)


def add_encoding_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_file_menu.py add_encoding_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.encoding_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_encoding_label"))
    for encoding in python_encodings_list:
        encoding_action = QAction(encoding, parent=ui_we_want_to_set.file_menu.encoding_menu)
        encoding_action.triggered.connect(
            lambda checked=False, action=encoding_action: set_encoding(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.encoding_menu.addAction(encoding_action)


def set_encoding(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info(f"build_file_menu.py set_encoding "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")
    ui_we_want_to_set.encoding = action.text()
    user_setting_dict.update({"encoding": action.text()})


def show_create_file_dialog(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_file_menu.py show_create_file_dialog "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.create_file_dialog = CreateFileDialog()
    ui_we_want_to_set.create_file_dialog.show()


def add_font_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_file_menu.py add_font_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.font_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_font_label"))
    for family in QFontDatabase().families():
        font_action = QAction(family, parent=ui_we_want_to_set.file_menu.font_menu)
        font_action.triggered.connect(lambda checked=False, action=font_action: set_font(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.font_menu.addAction(font_action)


def set_font(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info(f"build_file_menu.py set_font "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.setStyleSheet(
        f"font-size: {ui_we_want_to_set.font().pointSize()}pt;"
        f"font-family: {action.text()};"
    )
    user_setting_dict.update({"ui_font": action.text()})


def add_font_size_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_file_menu.py add_font_size_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.font_size_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_font_size_label"))
    for size in range(12, 38, 2):
        font_action = QAction(str(size), parent=ui_we_want_to_set.file_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font_size(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.font_size_menu.addAction(font_action)


def set_font_size(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info(f"build_file_menu.py set_font_size "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")
    ui_we_want_to_set.setStyleSheet(
        f"font-size: {int(action.text())}pt;"
        f"font-family: {ui_we_want_to_set.font().family()};"
    )
    user_setting_dict.update({"ui_font_size": int(action.text())})

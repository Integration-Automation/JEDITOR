from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_language_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_language_server.py set_language_menu ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.language_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("language_menu_label")
    )
    ui_we_want_to_set.language_menu.change_to_english_language_action = QAction(
        language_wrapper.language_word_dict.get("language_menu_bar_english")
    )
    ui_we_want_to_set.language_menu.change_to_english_language_action.triggered.connect(
        lambda: set_language("English", ui_we_want_to_set)
    )
    ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action = QAction(
        language_wrapper.language_word_dict.get("language_menu_bar_traditional_chinese")
    )
    ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action.triggered.connect(
        lambda: set_language("Traditional_Chinese", ui_we_want_to_set)
    )
    ui_we_want_to_set.language_menu.addAction(
        ui_we_want_to_set.language_menu.change_to_english_language_action
    )
    ui_we_want_to_set.language_menu.addAction(
        ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action
    )


def set_language(language: str, ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_language_server.py set_language "
                        f"language: {language} "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    language_wrapper.reset_language(language)
    user_setting_dict.update({"language": language})
    message_box = QMessageBox(ui_we_want_to_set)
    message_box.setText(language_wrapper.language_word_dict.get("language_menu_bar_please_restart_messagebox"))
    message_box.show()

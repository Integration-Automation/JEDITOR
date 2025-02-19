from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_help_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_help_menu.py set_help_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.help_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("help_menu_label"))
    ui_we_want_to_set.help_menu.help_github_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_github_label"))
    ui_we_want_to_set.help_menu.help_github_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://github.com/Integrated-Testing-Environment/je_editor",
            language_wrapper.language_word_dict.get("help_menu_open_github_label"))
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_github_action)

    ui_we_want_to_set.help_menu.help_doc_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_doc_label"))
    ui_we_want_to_set.help_menu.help_doc_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://je-editor.readthedocs.io/en/latest/",
            language_wrapper.language_word_dict.get("help_menu_open_doc_label"))
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_doc_action)

    ui_we_want_to_set.help_menu.help_about_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_about_label"))
    ui_we_want_to_set.help_menu.help_about_action.triggered.connect(
        show_about
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_about_action)


def open_web_browser(ui_we_want_to_set: EditorMain, url: str, tab_name: str):
    jeditor_logger.info("build_help_menu.py open_web_browser "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"url: {url} "
                        f"tab_name: {tab_name}")
    ui_we_want_to_set.tab_widget.addTab(
        BrowserWidget(start_url=url),
        f"{tab_name}{ui_we_want_to_set.tab_widget.count()}"
    )


def show_about():
    jeditor_logger.info("build_help_menu.py show_about")
    message_box = QMessageBox()
    message_box.setText(
        """
JEditor
Create by JE-Chen 2020 ~ Now
        """
    )
    message_box.exec()

from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.browser.browser_widget import JEBrowser

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_help_menu(ui_we_want_to_set: EditorMain) -> None:
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
    # Open Doc
    ui_we_want_to_set.help_menu.open_bing_gpt_menu_doc_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_re_edge_gpt_doc_label"))
    ui_we_want_to_set.help_menu.open_bing_gpt_menu_doc_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://reedgegpt.readthedocs.io/en/latest/",
            "ReEdgeGPT Doc"
        )
    )
    ui_we_want_to_set.help_menu.addAction(
        ui_we_want_to_set.help_menu.open_bing_gpt_menu_doc_action
    )
    # Open Github
    ui_we_want_to_set.help_menu.open_re_edge_gpt_github_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_re_edge_gpt_github_label"))
    ui_we_want_to_set.help_menu.open_re_edge_gpt_github_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://github.com/Integration-Automation/ReEdgeGPT",
            "ReEdgeGPT GitHub"
        )
    )
    ui_we_want_to_set.help_menu.addAction(
        ui_we_want_to_set.help_menu.open_re_edge_gpt_github_action
    )


def open_web_browser(ui_we_want_to_set: EditorMain, url: str, tab_name: str):
    ui_we_want_to_set.tab_widget.addTab(
        JEBrowser(start_url=url),
        f"{tab_name}{ui_we_want_to_set.tab_widget.count()}"
    )


def show_about():
    message_box = QMessageBox()
    message_box.setText(
        """
JEditor
Create by JE-Chen 2020 ~ Now
        """
    )
    message_box.exec()

from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.browser.je_broser import JEBrowser

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox


def set_help_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.help_menu = ui_we_want_to_set.menu.addMenu("Help")
    ui_we_want_to_set.help_menu.help_github_action = QAction("GitHub")
    ui_we_want_to_set.help_menu.help_github_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://github.com/Integrated-Testing-Environment/je_editor", "GitHub")
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_github_action)

    ui_we_want_to_set.help_menu.help_doc_action = QAction("Doc")
    ui_we_want_to_set.help_menu.help_doc_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://je-editor.readthedocs.io/en/latest/", "Doc")
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_doc_action)

    ui_we_want_to_set.help_menu.help_about_action = QAction("About")
    ui_we_want_to_set.help_menu.help_about_action.triggered.connect(
        show_about
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_about_action)


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

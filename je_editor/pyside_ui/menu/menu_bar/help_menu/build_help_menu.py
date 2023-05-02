import webbrowser

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox


def set_help_menu(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.help_menu .help_github_action = QAction("GitHub")
    ui_we_want_to_set.help_menu .help_github_action.triggered.connect(
        lambda: open_web_browser("https://github.com/Integrated-Testing-Environment/je_editor")
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu .help_github_action)

    ui_we_want_to_set.help_menu .help_doc_action = QAction("Doc")
    ui_we_want_to_set.help_menu .help_doc_action.triggered.connect(
        lambda: open_web_browser("https://je-editor.readthedocs.io/en/latest/")
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu .help_doc_action)

    ui_we_want_to_set.help_menu .help_about_action = QAction("About")
    ui_we_want_to_set.help_menu .help_about_action.triggered.connect(
        show_about
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_about_action)


def open_web_browser(url: str):
    webbrowser.open(url=url)


def show_about():
    message_box = QMessageBox()
    message_box.setText(
        """
JEditor
Create by JE-Chen
        """
    )
    message_box.exec()

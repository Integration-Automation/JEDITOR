from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMessageBox, QInputDialog

from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager


def set_venv_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.venv_menu = ui_we_want_to_set.menu.addMenu("Venv")
    # Create an venv
    ui_we_want_to_set.venv_menu.create_venv_action = QAction("Create Venv")
    ui_we_want_to_set.venv_menu.create_venv_action.setShortcut(
        "Ctrl+v"
    )
    ui_we_want_to_set.venv_menu.create_venv_action.triggered.connect(
        lambda: create_venv(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.create_venv_action)
    # pip upgrade package
    ui_we_want_to_set.venv_menu.pip_upgrade_action = QAction("pip upgrade package")
    ui_we_want_to_set.venv_menu.pip_upgrade_action.setShortcut(
        "Ctrl+p"
    )
    ui_we_want_to_set.venv_menu.pip_upgrade_action.triggered.connect(
        lambda: pip_install_package_update(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_upgrade_action)
    # pip package
    ui_we_want_to_set.venv_menu.pip_action = QAction("pip package")
    ui_we_want_to_set.venv_menu.pip_action.setShortcut(
        QKeySequence(Qt.Key.Key_P, Qt.Key.Key_U)
    )
    ui_we_want_to_set.venv_menu.pip_action.triggered.connect(
        lambda: pip_install_package(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_action)


def create_venv(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            create_venv_shell = ShellManager(main_window=widget)
            create_venv_shell.later_init()
            create_venv_shell.exec_shell(
                [f"{create_venv_shell.compiler_path}", "-m", "venv", "venv"]
            )
            print("Creating venv please waiting for shell exit code.")
        else:
            message_box = QMessageBox()
            message_box.setText("venv already exists.")
            message_box.exec()


def shell_pip_install(ui_we_want_to_set: EditorMain, pip_install_command_list: list):
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            message_box = QMessageBox()
            message_box.setText("Please create venv first.")
            message_box.exec()
        else:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set, "Install Package", "What Package you want to install"
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    pip_install_command_list
                )


def detect_venv() -> bool:
    venv_path = Path(os.getcwd() + "/venv")
    if not venv_path.exists():
        message_box = QMessageBox()
        message_box.setText("Please create venv first.")
        message_box.exec()
        return False
    return True


def pip_install_package_update(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        if detect_venv:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set, "Install Package", "What Package you want to install or update"
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}", "-U"]
                )


def pip_install_package(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        if detect_venv:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set, "Install Package", "What Package you want to install"
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}"]
                )

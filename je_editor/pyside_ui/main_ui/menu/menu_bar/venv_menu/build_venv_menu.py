import os
from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QInputDialog

from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager


def set_venv_menu(ui_we_want_to_set: QMainWindow) -> None:
    # Create an venv
    ui_we_want_to_set.venv_menu.create_venv_action = QAction("Create Venv")
    ui_we_want_to_set.venv_menu.create_venv_action.setShortcut(
        "Ctrl+v"
    )
    ui_we_want_to_set.venv_menu.create_venv_action.triggered.connect(
        lambda: create_venv(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.create_venv_action)
    # PIP a package
    ui_we_want_to_set.venv_menu.pip_action = QAction("pip package")
    ui_we_want_to_set.venv_menu.pip_action.setShortcut(
        "Ctrl+p"
    )
    ui_we_want_to_set.venv_menu.pip_action.triggered.connect(
        lambda: pip_install_package(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_action)


def create_venv(ui_we_want_to_set: QMainWindow) -> None:
    venv_path = Path(os.getcwd() + "/venv")
    if not venv_path.exists():
        create_venv_shell = ShellManager(main_window=ui_we_want_to_set)
        create_venv_shell.later_init()
        create_venv_shell.exec_shell(
            [f"{create_venv_shell.compiler_path}",  "-m", "venv", "venv"]
        )
        print("Creating venv please waiting for shell exit code.")
    else:
        message_box = QMessageBox()
        message_box.setText("venv already exists.")
        message_box.exec()


def pip_install_package(ui_we_want_to_set: QMainWindow) -> None:
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
            pip_install_shell = ShellManager(main_window=ui_we_want_to_set)
            pip_install_shell.later_init()
            pip_install_shell.exec_shell(
                [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}"]
            )

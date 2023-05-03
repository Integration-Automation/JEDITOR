import os
import sys
from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox

from je_editor.pyside_ui.file_dialog.open_file_dialog import choose_file_get_open_filename
from je_editor.pyside_ui.file_dialog.save_file_dialog import choose_file_get_save_filename
from je_editor.pyside_ui.shell_process.shell_exec import shell_manager


def set_file_menu(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.file_menu.open_file_action = QAction("Open File")
    ui_we_want_to_set.file_menu.open_file_action.setShortcut(
        "Ctrl+o"
    )
    ui_we_want_to_set.file_menu.open_file_action.triggered.connect(
        lambda: choose_file_get_open_filename(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_file_action)
    ui_we_want_to_set.file_menu.save_file_action = QAction("Save File")
    ui_we_want_to_set.file_menu.save_file_action.setShortcut(
        "Ctrl+s"
    )
    ui_we_want_to_set.file_menu.save_file_action.triggered.connect(
        lambda: choose_file_get_save_filename(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.save_file_action)
    ui_we_want_to_set.file_menu.venv_menu = ui_we_want_to_set.file_menu.addMenu("Venv")
    ui_we_want_to_set.file_menu.venv_menu.create_venv_action = QAction("Create Venv")
    ui_we_want_to_set.file_menu.venv_menu.create_venv_action.setShortcut(
        "Ctrl+v"
    )
    ui_we_want_to_set.file_menu.venv_menu.create_venv_action.triggered.connect(
        create_venv
    )
    ui_we_want_to_set.file_menu.venv_menu.addAction(ui_we_want_to_set.file_menu.venv_menu.create_venv_action)
    # Activate Venv menu
    ui_we_want_to_set.file_menu.venv_menu.activate_menu \
        = ui_we_want_to_set.file_menu.venv_menu.addMenu("Activate Venv")
    activate_menu = ui_we_want_to_set.file_menu.venv_menu.activate_menu
    if sys.platform in ["win32", "cygwin", "msys"]:
        activate_menu.activate_cmd_action = QAction("Activate using cmd")
        activate_menu.activate_cmd_action.triggered.connect(
            lambda: activate_venv(
                activate_command="",
                path="/venv/Scripts/activate.bat"
            )
        )
        activate_menu.addAction(activate_menu.activate_cmd_action)
        activate_menu.activate_power_shell_action = QAction("Activate using Power Shell")
        activate_menu.activate_power_shell_action.triggered.connect(
            lambda: activate_venv(
                activate_command="",
                path="/venv/Scripts/Activate.ps1"
            )
        )
        activate_menu.addAction(activate_menu.activate_power_shell_action)
    else:
        activate_menu.activate_bash_action = QAction("Activate using bash")
        activate_menu.activate_bash_action.triggered.connect(
            lambda: activate_venv(
                activate_command="source ",
                path="/venv//bin/activate"
            )
        )
        activate_menu.addAction(activate_menu.activate_bash_action)
        activate_menu.activate_fish_action = QAction("Activate using fish")
        activate_menu.activate_fish_action.triggered.connect(
            lambda: activate_venv(
                activate_command="source ",
                path="/venv/bin/activate.fish"
            )
        )
        activate_menu.addAction(activate_menu.activate_fish_action)
        activate_menu.activate_csh_action = QAction("Activate using csh")
        activate_menu.activate_csh_action.triggered.connect(
            lambda: activate_venv(
                activate_command="source ",
                path="/venv/bin/activate.csh"
            )
        )
        activate_menu.addAction(activate_menu.activate_csh_action)
        activate_menu.activate_posix_power_shell_action = QAction("Activate using Posix Power Shell")
        activate_menu.activate_posix_power_shell_action.triggered.connect(
            lambda: activate_venv(
                activate_command="",
                path="/venv/bin/Activate.ps1"
            )
        )
        activate_menu.addAction(activate_menu.activate_posix_power_shell_action)


def create_venv():
    venv_path = Path(os.getcwd() + "/venv")
    if not venv_path.exists():
        shell_manager.exec_shell("python -m venv " + "venv")
    else:
        message_box = QMessageBox()
        message_box.setText("Venv already exists")
        message_box.exec()


def activate_venv(activate_command: str, path: str):
    activate_path = Path(os.getcwd() + path)
    print(activate_command + str(activate_path))
    shell_manager.exec_shell(activate_command + " " + str(activate_path))

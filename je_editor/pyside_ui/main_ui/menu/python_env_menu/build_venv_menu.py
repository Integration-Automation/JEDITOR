from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
import os
from pathlib import Path

from PySide6.QtGui import QAction, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog

from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_venv_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py set_venv_menu ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.venv_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("python_env_menu_label"))
    # Create an venv
    ui_we_want_to_set.venv_menu.change_language_menu = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_create_venv_label"))
    ui_we_want_to_set.venv_menu.change_language_menu.setShortcut(
        QKeySequence("Ctrl+Shift+V")
    )
    ui_we_want_to_set.venv_menu.change_language_menu.triggered.connect(
        lambda: create_venv(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.change_language_menu)
    # pip upgrade package
    ui_we_want_to_set.venv_menu.pip_upgrade_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_pip_upgrade_label")
    )
    ui_we_want_to_set.venv_menu.pip_upgrade_action.setShortcut(
        QKeySequence("Ctrl+Shift+U")
    )
    ui_we_want_to_set.venv_menu.pip_upgrade_action.triggered.connect(
        lambda: pip_install_package_update(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_upgrade_action)
    # pip package
    ui_we_want_to_set.venv_menu.pip_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_pip_label"))
    ui_we_want_to_set.venv_menu.pip_action.setShortcut(
        QKeySequence("Ctrl+Shift+P")
    )
    ui_we_want_to_set.venv_menu.pip_action.triggered.connect(
        lambda: pip_install_package(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_action)
    # choose python interpreter
    ui_we_want_to_set.venv_menu.choose_interpreter_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_choose_interpreter_label"))
    ui_we_want_to_set.venv_menu.choose_interpreter_action.triggered.connect(
        lambda: chose_python_interpreter(ui_we_want_to_set)
    )
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.choose_interpreter_action)


def create_venv(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py create_venv ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            create_venv_shell = ShellManager(main_window=widget, after_done_function=widget.code_edit.check_env,
                                             shell_encoding=ui_we_want_to_set.encoding)
            create_venv_shell.later_init()
            create_venv_shell.exec_shell(
                [f"{create_venv_shell.compiler_path}", "-m", "venv", "venv"]
            )
            text_cursor =  widget.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(
                language_wrapper.language_word_dict.get("python_env_menu_creating_venv_message"), text_format)
            text_cursor.insertBlock()
        else:
            message_box = QMessageBox()
            message_box.setText(
                language_wrapper.language_word_dict.get("python_env_menu_venv_exists"))
            message_box.exec()


def shell_pip_install(ui_we_want_to_set: EditorMain, pip_install_command_list: list):
    jeditor_logger.info("build_venv_menu.py create_venv "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"pip_install_command_list: {pip_install_command_list}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            message_box = QMessageBox()
            message_box.setText(language_wrapper.language_word_dict.get("python_env_menu_please_create_venv"))
            message_box.exec()
        else:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_label")
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget, shell_encoding=ui_we_want_to_set.encoding)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    pip_install_command_list
                )


def detect_venv() -> bool:
    jeditor_logger.info("build_venv_menu.py detect_venv")
    venv_path = Path(os.getcwd() + "/venv")
    if not venv_path.exists():
        message_box = QMessageBox()
        message_box.setText(language_wrapper.language_word_dict.get("python_env_menu_please_create_venv"))
        message_box.exec()
        return False
    return True


def pip_install_package_update(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py pip_install_package_update ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        if detect_venv:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_or_update_package_messagebox_label")
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget, after_done_function=widget.code_edit.check_env,
                                                 shell_encoding=ui_we_want_to_set.encoding)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}", "-U"]
                )


def pip_install_package(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py pip_install_package ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        if detect_venv:
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_label")
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget, after_done_function=widget.code_edit.check_env,
                                                 shell_encoding=ui_we_want_to_set.encoding)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}"]
                )


def chose_python_interpreter(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_venv_menu.py chose_python_interpreter ui_we_want_to_set: {ui_we_want_to_set}")
    file_path = QFileDialog().getOpenFileName(
        parent=ui_we_want_to_set,
        dir=str(Path.cwd())
    )[0]
    if file_path is not None and file_path != "":
        ui_we_want_to_set.python_compiler = file_path
        user_setting_dict.update({"python_compiler": file_path})

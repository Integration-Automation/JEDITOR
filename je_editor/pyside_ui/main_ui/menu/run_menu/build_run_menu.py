from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction, QKeySequence, Qt
from PySide6.QtWidgets import QMessageBox

from je_editor.pyside_ui.code.code_process.code_exec import ExecManager, run_instance_manager
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager


def set_run_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu("Run")
    ui_we_want_to_set.run_menu.run_program_action = QAction("Run Program")
    ui_we_want_to_set.run_menu.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.run_program_action.setShortcut(
        QKeySequence(Qt.Key.Key_R, Qt.Key.Key_F1)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_program_action)
    ui_we_want_to_set.run_menu.run_on_shell_action = QAction("Run On Shell")
    ui_we_want_to_set.run_menu.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.run_on_shell_action.setShortcut(
        QKeySequence(Qt.Key.Key_R, Qt.Key.Key_F2)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_on_shell_action)
    ui_we_want_to_set.run_menu.clean_result_action = QAction("Clean Result")
    ui_we_want_to_set.run_menu.clean_result_action.triggered.connect(
        lambda: clean_result(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.clean_result_action.setShortcut(
        QKeySequence(Qt.Key.Key_R, Qt.Key.Key_F3)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.clean_result_action)

    ui_we_want_to_set.run_menu.stop_program_action = QAction("Stop Program")
    ui_we_want_to_set.run_menu.stop_program_action.triggered.connect(
        stop_program
    )
    ui_we_want_to_set.run_menu.stop_program_action.setShortcut(
        QKeySequence(Qt.Key.Key_R, Qt.Key.Key_F4)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_program_action)
    # Run help menu
    ui_we_want_to_set.run_menu.run_help_menu = ui_we_want_to_set.run_menu.addMenu("Run Help")
    # Run help action
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action = QAction("Run Help")
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action.triggered.connect(
        show_run_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.run_help_action)
    # Shell help action
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action = QAction("Shell Help")
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action.triggered.connect(
        show_shell_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.shell_help_action)


def run_program(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if choose_file_get_save_file_path(ui_we_want_to_set):
            code_exec = ExecManager(widget)
            code_exec.later_init()
            code_exec.exec_code(
                widget.current_file
            )


def shell_exec(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        shell_command = ShellManager(
            main_window=widget,
            shell_encoding=ui_we_want_to_set.encoding)
        shell_command.later_init()
        shell_command.exec_shell(
            widget.code_edit.toPlainText()
        )


def stop_program() -> None:
    run_instance_manager.close_all_instance()


def clean_result(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.code_result.setPlainText("")


def show_run_help() -> None:
    message_box = QMessageBox()
    message_box.setText(
        """
If you are unable to run a Python program, please make sure you are not using the default system Python.
(For Windows, you can use the Windows Store or Venv.)
(For Linux & MacOS, you can use Venv.)
        """
    )
    message_box.exec()


def show_shell_help() -> None:
    message_box = QMessageBox()
    message_box.setText(
        """
When executing a shell command, if you encounter a decoding error, 
please make sure that the current encoding is consistent with the default encoding of the system shell.
        """
    )
    message_box.exec()

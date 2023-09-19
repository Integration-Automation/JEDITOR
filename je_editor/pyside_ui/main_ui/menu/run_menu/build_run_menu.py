from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.debugger_input import DebuggerInput
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_run_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_label"))
    # Run program
    ui_we_want_to_set.run_menu.run_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_program_label"))
    ui_we_want_to_set.run_menu.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_program_action)
    # Debug menu inside run menu
    ui_we_want_to_set.debug_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("editor_debugger"))
    # Run debugger
    ui_we_want_to_set.debug_menu.run_debugger_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_debugger"))
    ui_we_want_to_set.debug_menu.run_debugger_action.triggered.connect(
        lambda: run_debugger(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.run_debugger_action)
    # Show debugger input
    ui_we_want_to_set.debug_menu.show_debugger_input = QAction(
        language_wrapper.language_word_dict.get("show_debugger_input"))
    ui_we_want_to_set.debug_menu.show_debugger_input.triggered.connect(
        lambda: show_debugger_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.show_debugger_input)
    # Run on shell
    ui_we_want_to_set.run_menu.run_on_shell_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_on_shell_label"))
    ui_we_want_to_set.run_menu.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    # Clean result
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.run_on_shell_action)
    ui_we_want_to_set.run_menu.clean_result_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_clear_result_label"))
    ui_we_want_to_set.run_menu.clean_result_action.triggered.connect(
        lambda: clean_result(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.clean_result_action)
    # Close program
    ui_we_want_to_set.run_menu.stop_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_stop_program_label"))
    ui_we_want_to_set.run_menu.stop_program_action.triggered.connect(
        lambda: stop_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_program_action)
    # Close all program
    ui_we_want_to_set.run_menu.stop_all_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_stop_all_program_label"))
    ui_we_want_to_set.run_menu.stop_all_program_action.triggered.connect(
        stop_all_program
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_all_program_action)
    # Run help menu
    ui_we_want_to_set.run_menu.run_help_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_help_label"))
    # Run help action
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_help_label"))
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action.triggered.connect(
        show_run_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.run_help_action)
    # Shell help action
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_shell_help_label"))
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action.triggered.connect(
        show_shell_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.shell_help_action)


def please_close_current_running_messagebox(ui_we_want_to_set: EditorMain):
    please_stop_current_running_program_messagebox = QMessageBox(ui_we_want_to_set)
    please_stop_current_running_program_messagebox.setText(
        language_wrapper.language_word_dict.get("please_stop_current_running_program")
    )
    please_stop_current_running_program_messagebox.show()


def run_program(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_program is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            if choose_file_get_save_file_path(ui_we_want_to_set):
                code_exec = ExecManager(widget)
                code_exec.later_init()
                code_exec.exec_code(
                    widget.current_file
                )
                widget.exec_program = code_exec
        else:
            please_close_current_running_messagebox(ui_we_want_to_set)


def run_debugger(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_python_debugger is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            if choose_file_get_save_file_path(ui_we_want_to_set):
                code_exec = ExecManager(widget)
                code_exec.later_init()
                code_exec.code_result = widget.debugger_result
                code_exec.exec_code(
                    widget.current_file, exec_prefix=["-m", "pdb"]
                )
                widget.exec_python_debugger = code_exec
                widget.debugger_input = DebuggerInput(widget)
                widget.debugger_input.show()
        else:
            please_close_current_running_messagebox(ui_we_want_to_set)


def show_debugger_input(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.debugger_input = DebuggerInput(widget)
        widget.debugger_input.show()


def shell_exec(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_shell is None:
            shell_command = ShellManager(
                main_window=widget,
                shell_encoding=ui_we_want_to_set.encoding)
            shell_command.later_init()
            shell_command.exec_shell(
                widget.code_edit.toPlainText()
            )
            widget.exec_shell = shell_command
        else:
            please_close_current_running_messagebox(ui_we_want_to_set)


def stop_program(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_program is not None:
            if widget.exec_program.process is not None:
                widget.exec_program.process.terminate()
            widget.exec_program = None
        if widget.exec_shell is not None:
            if widget.exec_shell.process is not None:
                widget.exec_shell.process.terminate()
            widget.exec_shell = None
        if widget.exec_python_debugger is not None:
            if widget.exec_python_debugger.process is not None:
                widget.exec_python_debugger.process.terminate()
            widget.exec_python_debugger = None


def stop_all_program() -> None:
    run_instance_manager.close_all_instance()


def clean_result(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.code_result.setPlainText("")


def show_run_help() -> None:
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_run_help_tip")
    )
    message_box.exec()


def show_shell_help() -> None:
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_shell_run_tip")
    )
    message_box.exec()

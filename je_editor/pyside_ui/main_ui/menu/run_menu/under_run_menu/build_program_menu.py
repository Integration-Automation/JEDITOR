from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.editor.process_input import ProcessInput
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import please_close_current_running_messagebox
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_program_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.run_program_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_program_label"))
    # Run program
    ui_we_want_to_set.run_program_menu.run_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_program_label"))
    ui_we_want_to_set.run_program_menu.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_program_menu.addAction(ui_we_want_to_set.run_program_menu.run_program_action)
    # Show shell input
    ui_we_want_to_set.run_program_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_program_input"))
    ui_we_want_to_set.run_program_menu.show_shell_input.triggered.connect(
        lambda: show_program_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_program_menu.addAction(ui_we_want_to_set.run_program_menu.show_shell_input)


def run_program(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_program is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            if choose_file_get_save_file_path(ui_we_want_to_set):
                code_exec = ExecManager(widget, program_encoding=ui_we_want_to_set.encoding)
                code_exec.later_init()
                code_exec.exec_code(
                    widget.current_file
                )
                widget.exec_program = code_exec
        else:
            please_close_current_running_messagebox(ui_we_want_to_set)


def show_program_input(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.program_input = ProcessInput(widget, "program")
        widget.program_input.show()

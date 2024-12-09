from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.editor.process_input import ProcessInput
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import please_close_current_running_messagebox
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction

from je_editor.pyside_ui.code.code_process.code_exec import ExecManager
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_debug_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py set_debug_menu ui_we_want_to_set: {ui_we_want_to_set}")
    # Debug menu inside run menu
    ui_we_want_to_set.debug_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))
    # Run debugger
    ui_we_want_to_set.debug_menu.run_debugger_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_debugger"))
    ui_we_want_to_set.debug_menu.run_debugger_action.triggered.connect(
        lambda: run_debugger(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.run_debugger_action)
    # Show debugger input
    ui_we_want_to_set.debug_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_debugger_input"))
    ui_we_want_to_set.debug_menu.show_shell_input.triggered.connect(
        lambda: show_debugger_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.show_shell_input)


def run_debugger(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py run_debugger ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        if widget.exec_python_debugger is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            if choose_file_get_save_file_path(ui_we_want_to_set):
                code_exec = ExecManager(widget, program_encoding=ui_we_want_to_set.encoding)
                code_exec.later_init()
                code_exec.code_result = widget.debugger_result
                code_exec.exec_code(
                    widget.current_file, exec_prefix=["-m", "pdb"]
                )
                widget.exec_python_debugger = code_exec
                widget.debugger_input = ProcessInput(widget)
                widget.debugger_input.show()
        else:
            please_close_current_running_messagebox(ui_we_want_to_set)


def show_debugger_input(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py show_debugger_input ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.debugger_input = ProcessInput(widget, "debugger")
        widget.debugger_input.show()

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_debug_menu import set_debug_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_program_menu import set_program_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_shell_menu import set_shell_menu
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_run_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py set_run_menu ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_label"))
    set_program_menu(ui_we_want_to_set)
    set_shell_menu(ui_we_want_to_set)
    set_debug_menu(ui_we_want_to_set)
    # Clean result
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


def stop_program(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py stop_program ui_we_want_to_set: {ui_we_want_to_set}")
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
    jeditor_logger.info(f"build_run_menu.py stop_all_program")
    run_instance_manager.close_all_instance()


def clean_result(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py clean_result ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.code_result.setPlainText("")


def show_run_help() -> None:
    jeditor_logger.info(f"build_run_menu.py show_run_help")
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_run_help_tip")
    )
    message_box.exec()


def show_shell_help() -> None:
    jeditor_logger.info(f"build_run_menu.py show_shell_help")
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_shell_run_tip")
    )
    message_box.exec()

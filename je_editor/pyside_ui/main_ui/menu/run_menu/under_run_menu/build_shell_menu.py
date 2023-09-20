from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.editor.process_input import ProcessInput
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import please_close_current_running_messagebox

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction

from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_shell_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.run_shell_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_on_shell_label"))
    # Run on shell
    ui_we_want_to_set.run_shell_menu.run_on_shell_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_on_shell_label"))
    ui_we_want_to_set.run_shell_menu.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_shell_menu.addAction(ui_we_want_to_set.run_shell_menu.run_on_shell_action)
    # Show shell input
    ui_we_want_to_set.run_shell_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_shell_input"))
    ui_we_want_to_set.run_shell_menu.show_shell_input.triggered.connect(
        lambda: show_shell_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_shell_menu.addAction(ui_we_want_to_set.run_shell_menu.show_shell_input)


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


def show_shell_input(ui_we_want_to_set: EditorMain) -> None:
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.shell_input = ProcessInput(widget, "shell")
        widget.shell_input.show()

from tkinter import Menu

from je_editor.ui.ui_event.clear_result.clear_result import clear_result_area
from je_editor.ui.ui_event.execute.execute_code.exec_code import stop_program
from je_editor.ui.ui_event.execute.execute_shell_command.run_on_shell import execute_shell_command


def build_run_menu(editor_instance):
    # Run menu
    editor_instance.run_menu = Menu(editor_instance.menu, tearoff=0)
    editor_instance.run_menu.add_command(
        label="Run Program",
        command=editor_instance.ui_execute_program
    )
    editor_instance.run_menu.add_command(
        label="Run on shell",
        command=lambda: execute_shell_command(
            editor_instance.program_run_result_textarea,
            editor_instance.code_editor_textarea
        )
    )
    editor_instance.run_menu.add_command(
        label="Stop Program",
        command=lambda: stop_program(editor_instance.exec_manager)
    )
    editor_instance.run_menu.add_command(
        label="Clean Result", command=lambda: clear_result_area(
            editor_instance.program_run_result_textarea
        )
    )

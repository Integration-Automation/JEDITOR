import tkinter

from je_editor.ui.ui_event.text_process.shell.shell_exec_manager import ShellManager


def execute_shell_command(code_editor: tkinter.Text, shell_manager: ShellManager):
    """
    :param program_run_result_textarea tkinter textarea to show result
    :param code_editor get the command to run
    :param shell_manager:
    """
    shell_manager.exec_shell(code_editor.get("1.0", "end-1c"))

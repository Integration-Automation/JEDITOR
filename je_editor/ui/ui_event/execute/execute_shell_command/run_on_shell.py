from tkinter import NORMAL
from tkinter import DISABLED

from je_editor.utils.text_process.shell.shell_text import run_on_shell
from je_editor.utils.text_process.program_exec.process_error import process_error_text


def execute_shell_command(run_result, code_editor):
    """
    :param run_result tkinter textarea to show result
    :param code_editor get the command to run
    """
    run_result.configure(state=NORMAL)
    run_result.delete("1.0", "end-1c")
    temp_result = run_on_shell(code_editor.get("1.0", "end-1c"))
    if temp_result[1]:
        process_error_text(run_result, temp_result[0])
    else:
        run_result.insert("1.0", temp_result[0])
    run_result.configure(state=DISABLED)

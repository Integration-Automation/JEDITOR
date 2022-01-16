from tkinter import NORMAL
from tkinter import DISABLED

from je_editor.ui.ui_event.text_process.shell.shell_text import run_on_shell
from je_editor.ui.ui_event.text_process.program_exec.process_error import process_error_text


def execute_shell_command(program_run_result_textarea, code_editor):
    """
    :param program_run_result_textarea tkinter textarea to show result
    :param code_editor get the command to run
    """
    program_run_result_textarea.configure(state=NORMAL)
    program_run_result_textarea.delete("1.0", "end-1c")
    temp_result = run_on_shell(code_editor.get("1.0", "end-1c"))
    if temp_result[1]:
        process_error_text(program_run_result_textarea, temp_result[0])
    else:
        program_run_result_textarea.insert("1.0", temp_result[0])
    program_run_result_textarea.configure(state=DISABLED)

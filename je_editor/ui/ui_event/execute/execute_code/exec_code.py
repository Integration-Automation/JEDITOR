from tkinter import NORMAL
from tkinter import DISABLED

from je_editor.utils.text_process.program_exec.exec_text import exec_code
from je_editor.utils.text_process.program_exec.process_error import process_error_text


def execute_code(run_result, current_file, save_function):
    """
    :param run_result tkinter textarea to show result
    :param current_file will execute file
    :param save_function if current_file is None or "" save and run
    """
    run_result.configure(state=NORMAL)
    run_result.delete("1.0", "end-1c")
    if current_file is not None and current_file != "":
        temp_result = exec_code(current_file)
        run_result.insert("1.0", temp_result[0])
        process_error_text(run_result, temp_result[1])
        run_result.configure(state=DISABLED)
    else:
        save_function()
        if current_file is not None and current_file != "":
            temp_result = exec_code(current_file)
            run_result.insert("1.0", temp_result[0])
            process_error_text(run_result, temp_result[1])
            run_result.configure(state=DISABLED)

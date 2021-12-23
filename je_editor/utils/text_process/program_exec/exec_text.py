import os.path
import shutil
import subprocess
import sys
from pathlib import Path

from je_editor.utils.exception.je_editor_exception_tag import file_not_fond_error
from je_editor.utils.exception.je_editor_exception_tag import python_not_found_error
from je_editor.utils.exception.je_editor_exceptions import JEditorExecException


def exec_code(exec_file_name):
    """
    :param exec_file_name: string file will open to run
    :return: if error return result and True else return result and False
    """
    reformat_os_file_path = os.path.abspath(exec_file_name)
    print(reformat_os_file_path)
    try:
        if not Path(exec_file_name).exists():
            raise JEditorExecException(file_not_fond_error)
    except OSError as error:
        raise JEditorExecException(error)
    python_path = shutil.which("python")
    if python_path is None:
        raise JEditorExecException(python_not_found_error)
    exec_command = reformat_os_file_path
    return_exec_result = ""
    return_error_result = ""
    process = subprocess.Popen([python_path + " ", exec_command],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=False)
    print("execute: " + reformat_os_file_path)
    exec_result, error_result = process.communicate()
    reformat_exec_result = str(exec_result, encoding="utf-8")
    reformat_error_result = str(error_result, encoding="utf-8")
    for exec_result_line in reformat_exec_result:
        if not exec_result_line.startswith('#'):
            return_exec_result = "".join([return_exec_result, exec_result_line])
    for error_result_line in reformat_error_result:
        if not error_result_line.startswith('#'):
            return_error_result = "".join([return_error_result, error_result_line])
    return return_exec_result, return_error_result

import subprocess

from je_editor.utils.exception.exceptions import JEditorRunOnShellException


def run_on_shell(run_source):
    """
    :param run_source: string command to run
    :return: if error return result and True else return result and False
    """
    try:
        exec_result = subprocess.getoutput(run_source)
        return exec_result, False
    except Exception as error:
        return str(error), True

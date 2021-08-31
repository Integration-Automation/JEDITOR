import subprocess

from je_editor.utils.exception.je_editor_exceptions import JEditorRunOnShellException


def run_on_shell(run_source):
    try:
        exec_result = subprocess.getoutput(run_source)
        return exec_result
    except Exception as error:
        return str(error)

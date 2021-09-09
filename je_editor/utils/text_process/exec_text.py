from contextlib import redirect_stdout
from io import StringIO

from je_editor.utils.exception.je_editor_exceptions import JEditorExecException


def exec_code(exec_source):
    """
    :param exec_source: string code to run
    :return: if error return result and True else return result and False
    """
    try:
        exec_string_io = StringIO()
        with redirect_stdout(exec_string_io):
            exec(exec_source)
        exec_result = exec_string_io.getvalue()
        return exec_result, False

    except Exception as error:
        return str(error), True

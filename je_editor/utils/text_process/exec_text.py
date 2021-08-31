from contextlib import redirect_stdout
from io import StringIO

from je_editor.utils.exception.je_editor_exceptions import JEditorExecException


def exec_code(exec_source):
    try:
        exec_string_io = StringIO()
        with redirect_stdout(exec_string_io):
            exec(exec_source)
        exec_result = exec_string_io.getvalue()
        return exec_result

    except Exception as error:
        return str(error)

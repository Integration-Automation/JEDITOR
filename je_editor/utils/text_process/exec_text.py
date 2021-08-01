from contextlib import redirect_stdout
from io import StringIO

from je_editor.utils.exception.je_editor_exceptions import JEditorExecException


def exec_code(exec_source, show_result_ui_function, show_result_error_function):
    try:
        exec_string_io = StringIO()
        with redirect_stdout(exec_string_io):
            exec(exec_source)
        exec_result = exec_string_io.getvalue()
        show_result_ui_function(exec_result)

    except Exception as error:
        show_result_error_function(str(error))
        raise JEditorExecException(str(error))

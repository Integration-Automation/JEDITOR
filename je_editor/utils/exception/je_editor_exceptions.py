import sys

from je_editor.utils.exception.je_editor_exception_tag import je_editor_error
from je_editor.utils.exception.je_editor_exception_tag import je_editor_exec_error
from je_editor.utils.exception.je_editor_exception_tag import je_editor_open_file_error
from je_editor.utils.exception.je_editor_exception_tag import je_editor_save_file_error
from je_editor.utils.exception.je_editor_exception_tag import je_editor_shell_error
from je_editor.utils.exception.je_editor_exception_tag import je_editor_content_file_error


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class JEditorException(Exception):

    def __init__(self, message=je_editor_error):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return "{}".format(self.message)


class JEditorExecException(JEditorException):

    def __init__(self, message=je_editor_exec_error):
        super().__init__(message)


class JEditorRunOnShellException(JEditorException):

    def __init__(self, message=je_editor_shell_error):
        super().__init__(message)


class JEditorSaveFileException(JEditorException):
    def __init__(self, message=je_editor_save_file_error):
        super().__init__(message)


class JEditorOpenFileException(JEditorException):
    def __init__(self, message=je_editor_open_file_error):
        super().__init__(message)


class JEditorContentFileException(JEditorException):
    def __init__(self, message=je_editor_content_file_error):
        super().__init__(message)

import sys


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class JEditorException(Exception):
    pass


class JEditorExecException(JEditorException):
    pass


class JEditorRunOnShellException(JEditorException):
    pass


class JEditorSaveFileException(JEditorException):
    pass


class JEditorOpenFileException(JEditorException):
    pass


class JEditorContentFileException(JEditorException):
    pass

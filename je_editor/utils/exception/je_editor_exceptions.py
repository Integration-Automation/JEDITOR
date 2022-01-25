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


class JEditorCantFindLanguageException(JEditorException):
    pass


class JEditorJsonException(JEditorException):
    pass

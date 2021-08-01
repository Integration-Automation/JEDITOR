import sys


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class JEditorException(Exception):

    def __init__(self, message="JEditor error"):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"{self.message}"


class JEditorExecException(Exception):

    def __init__(self, message="JEditor exec error"):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"{self.message}"


class JEditorRunOnShellException(Exception):

    def __init__(self, message="JEditor run on shell error"):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f"{self.message}"

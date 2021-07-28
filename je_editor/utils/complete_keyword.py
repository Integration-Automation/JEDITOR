from PyQt5 import QtCore
from PyQt5.QtWidgets import QCompleter

keyword = [
    "False",
    "def",
    "if",
    "raise",
    "None",
    "del",
    "import",
    "return",
    "True",
    "elif",
    "in",
    "try",
    "and",
    "else",
    "is",
    "while",
    "as",
    "except",
    "lambda",
    "with",
    "assert",
    "finally",
    "nonlocal",
    "yield",
    "break",
    "for",
    "not",
    "class",
    "from",
    "or",
    "continue",
    "global",
    "pass"
]


class AutoComplete(QCompleter):
    insert_text = QtCore.pyqtSignal(str)

    def __init__(self, another_keyword=None, parent=None):
        self.last_select = "you should not use this before set"
        if another_keyword is not None:
            QCompleter.__init__(self, another_keyword, parent)
        else:
            QCompleter.__init__(self, keyword, parent)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.highlighted.connect(self.set_highlighted)

    def set_highlighted(self, text):
        self.last_select = text

    def get_select(self):
        return self.last_select


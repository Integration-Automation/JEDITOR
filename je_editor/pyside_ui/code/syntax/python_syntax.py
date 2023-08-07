from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor
from PySide6.QtGui import QFont
from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtGui import QTextCharFormat

keywords = [
    "False", "None", "True", "and", "as", "assert", "async",
    "await", "break", "class", "continue", "def", "del",
    "elif", "else", "except", "finally", "for", "from",
    "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"
]

builtins_keyword = [
    "abs", "aiter", "all", "any", "anext", "ascii",
    "bin", "bool", "breakpoint", "bytearray", "bytes",
    "callable", "chr", "classmethod", "compile", "complex",
    "delattr", "dict", "dir", "divmod",
    "enumerate", "eval", "exec",
    "filter", "float", "format", "frozenset",
    "getattr", "globals",
    "hasattr", "hash", "help", "hex",
    "id", "input", "int", "isinstance", "issubclass", "iter",
    "len", "list", "locals",
    "map", "max", "memoryview", "min",
    "next",
    "object", "oct", "open", "ord",
    "pow", "print", "property",
    "range", "repr", "reversed", "round",
    "set", "setattr", "slice", "sorted", "staticmethod",
    "str", "sum", "super",
    "tuple", "type",
    "vars",
    "zip",
    "__import__"
]

# Regex pattern

string_rule = [
    r"'''^.*(?:[^\\']|\\\\|\\')*.*$'''",  # 3* Singel
    r'"""^.*(?:[^\\"]|\\\\|\\")*.*$"""',  # 3* Double
    r"'[^'\\]*(\\.[^'\\]*)*'",  # Singel
    r'"[^"\\]*(\\.[^"\\]*)*"'  # Double
]

number_rule = [
    r"\b[+-]?[0-9]+[lL]?\b",
    r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b",
    r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"
]


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlight_rules = []

        # Highlight keywords
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(255, 212, 102))
        text_char_format.setFontWeight(QFont.Bold)
        for word in keywords:
            pattern = QRegularExpression(rf"\b{word}\b")
            self.highlight_rules.append((pattern, text_char_format))

        # Highlight builtins
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(0, 255, 255))
        for word in builtins_keyword:
            pattern = QRegularExpression(rf"\b{word}\b")
            self.highlight_rules.append((pattern, text_char_format))

        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(255, 255, 255))
        pattern = QRegularExpression(r"#[^\n]*")
        self.highlight_rules.append((pattern, text_char_format))

        # Highlight self
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(204, 0, 204))
        pattern = QRegularExpression(r"\bself\b")
        self.highlight_rules.append((pattern, text_char_format))

        # Highlight numbers
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(0, 128, 255))
        for rule in number_rule:
            pattern = QRegularExpression(rule)
            self.highlight_rules.append((pattern, text_char_format))

        # Highlight strings
        text_char_format = QTextCharFormat()
        text_char_format.setForeground(QColor(0, 153, 0))
        for rule in string_rule:
            pattern = QRegularExpression(rule)
            self.highlight_rules.append((pattern, text_char_format))

    def highlightBlock(self, text) -> None:
        for pattern, format in self.highlight_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
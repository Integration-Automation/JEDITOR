from PySide6.QtGui import QColor

syntax_rule_setting_dict: dict = {
    "number_rule": {
        "rules": (r"\b[+-]?[0-9]+[lL]?\b",
                  r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b",
                  r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"),
        "color": QColor(0, 128, 255)
    },
    "comment_rule": {
        "rules": (r"#[^\n]*",),
        "color": QColor(179, 204, 204)
    },
    "string_rule": {
        "rules": (
            r"'[^'\\]*(\\.[^'\\]*)*'",  # Singel
            r'"[^"\\]*(\\.[^"\\]*)*"',  # Double
        ),
        "color": QColor(0, 153, 0)
    }
}

syntax_word_setting_dict: dict = {
    "keywords": {
        "words": (
            "False", "None", "True", "and", "as", "assert", "async",
            "await", "break", "class", "continue", "def", "del",
            "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal",
            "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"
        ),
        "color": QColor(255, 212, 102)
    },
    "builtins_keyword": {
        "words": (
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
        ),
        "color": QColor(0, 255, 255)
    },
    "self": {
        "words": ("self",),
        "color": QColor(204, 0, 204)
    }

}

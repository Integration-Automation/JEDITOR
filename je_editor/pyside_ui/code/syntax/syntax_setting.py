from PySide6.QtGui import QColor

# -----------------------------
# 基本語法規則設定 (數字、註解、字串)
# Basic syntax rule settings (numbers, comments, strings)
# -----------------------------
syntax_rule_setting_dict: dict = {
    "number_rule": {
        # 數字規則 (整數、十六進位、小數/科學記號)
        # Number rules (integer, hex, float/scientific notation)
        "rules": (
            r"\b[+-]?[0-9]+[lL]?\b",                       # 整數 integer
            r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b",            # 十六進位 hex
            r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b"  # 浮點數/科學記號 float/scientific
        ),
        "color": QColor(0, 128, 255)  # 藍色 Blue
    },
    "comment_rule": {
        # 註解規則 (以 # 開頭直到換行)
        # Comment rule (starts with # until newline)
        "rules": (r"#[^\n]*",),
        "color": QColor(0, 230, 0)  # 綠色 Green
    },
    "string_rule": {
        # 字串規則 (單引號與雙引號)
        # String rules (single and double quotes)
        "rules": (
            r"'[^'\\]*(\\.[^'\\]*)*'",  # 單引號字串 single-quoted string
            r'"[^"\\]*(\\.[^"\\]*)*"',  # 雙引號字串 double-quoted string
        ),
        "color": QColor(0, 153, 0)  # 深綠色 Dark green
    }
}

# -----------------------------
# 關鍵字與內建函式設定
# Keywords and built-in functions
# -----------------------------
syntax_word_setting_dict: dict = {
    "keywords": {
        # Python 保留字 (語法關鍵字)
        # Python reserved keywords
        "words": (
            "False", "None", "True", "and", "as", "assert", "async",
            "await", "break", "class", "continue", "def", "del",
            "elif", "else", "except", "finally", "for", "from",
            "global", "if", "import", "in", "is", "lambda", "nonlocal",
            "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"
        ),
        "color": QColor(255, 212, 102)  # 黃色 Yellow
    },
    "builtins_keyword": {
        # Python 內建函式與型別
        # Python built-in functions and types
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
        "color": QColor(0, 255, 255)  # 青色 Cyan
    },
    "self": {
        # Python 類別中的 self 關鍵字
        # "self" keyword in Python classes
        "words": ("self",),
        "color": QColor(204, 0, 204)  # 紫色 Purple
    }
}

# -----------------------------
# 擴展語法設定 (其他語言可在此加入)
# Extended syntax settings (for other languages)
# -----------------------------
syntax_extend_setting_dict: dict = {
    # 目前為空，可依副檔名新增規則
    # Currently empty, can add rules for other file suffixes
}
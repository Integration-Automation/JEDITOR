"""
C++ 語法高亮插件 / C++ Syntax Highlighting Plugin

使用方式 / Usage:
    將此檔案複製到 jeditor_plugins/ 目錄下，重啟編輯器即可。
    Copy this file to jeditor_plugins/ directory and restart the editor.
"""
from PySide6.QtGui import QColor

from je_editor.plugins import register_programming_language

# C++ 關鍵字設定 / C++ keyword settings
cpp_syntax_words: dict = {
    "keywords": {
        # C++ 保留字 / C++ reserved keywords
        "words": (
            "alignas", "alignof", "and", "and_eq", "asm", "auto",
            "bitand", "bitor", "bool", "break",
            "case", "catch", "char", "char8_t", "char16_t", "char32_t",
            "class", "compl", "concept", "const", "consteval", "constexpr",
            "constinit", "const_cast", "continue", "co_await", "co_return", "co_yield",
            "decltype", "default", "delete", "do", "double", "dynamic_cast",
            "else", "enum", "explicit", "export", "extern",
            "false", "float", "for", "friend",
            "goto",
            "if", "inline", "int",
            "long",
            "mutable",
            "namespace", "new", "noexcept", "not", "not_eq", "nullptr",
            "operator", "or", "or_eq",
            "private", "protected", "public",
            "register", "reinterpret_cast", "requires", "return",
            "short", "signed", "sizeof", "static", "static_assert",
            "static_cast", "struct", "switch",
            "template", "this", "thread_local", "throw", "true", "try",
            "typedef", "typeid", "typename",
            "union", "unsigned", "using",
            "virtual", "void", "volatile",
            "wchar_t", "while",
            "xor", "xor_eq",
        ),
        "color": QColor(255, 212, 102),  # 黃色 Yellow
    },
    "preprocessor": {
        # 預處理器指令 / Preprocessor directives
        "words": (
            "include", "define", "undef", "ifdef", "ifndef",
            "if", "elif", "else", "endif", "pragma", "error", "warning",
        ),
        "color": QColor(255, 128, 0),  # 橙色 Orange
    },
    "stl_types": {
        # 常用 STL 型別 / Common STL types
        "words": (
            "string", "vector", "map", "unordered_map", "set", "unordered_set",
            "list", "deque", "queue", "stack", "priority_queue",
            "pair", "tuple", "array", "bitset",
            "shared_ptr", "unique_ptr", "weak_ptr",
            "optional", "variant", "any",
            "cout", "cin", "cerr", "endl",
            "size_t", "ptrdiff_t", "int8_t", "int16_t", "int32_t", "int64_t",
            "uint8_t", "uint16_t", "uint32_t", "uint64_t",
        ),
        "color": QColor(0, 255, 255),  # 青色 Cyan
    },
}

# C++ 額外語法規則 / C++ extra syntax rules
cpp_syntax_rules: dict = {
    "single_line_comment": {
        # 單行註解 // / Single-line comment //
        "rules": (r"//[^\n]*",),
        "color": QColor(0, 230, 0),  # 綠色 Green
    },
    "multi_line_comment_single_line": {
        # 多行註解在同一行 / Multi-line comment on single line
        "rules": (r"/\*.*?\*/",),
        "color": QColor(0, 230, 0),  # 綠色 Green
    },
    "preprocessor_directive": {
        # 預處理器 # 開頭 / Preprocessor # prefix
        "rules": (r"#\s*\w+",),
        "color": QColor(255, 128, 0),  # 橙色 Orange
    },
    "char_literal": {
        # 字元常量 / Character literal
        "rules": (r"'[^'\\]*(\\.[^'\\]*)*'",),
        "color": QColor(0, 153, 0),  # 深綠色 Dark green
    },
}


def register() -> None:
    """
    註冊 C++ 語法高亮插件。
    Register the C++ syntax highlighting plugin.
    支援副檔名 / Supported suffixes: .cpp, .cxx, .cc, .h, .hpp, .hxx
    """
    for suffix in (".cpp", ".cxx", ".cc", ".h", ".hpp", ".hxx"):
        register_programming_language(
            suffix=suffix,
            syntax_words=cpp_syntax_words,
            syntax_rules=cpp_syntax_rules,
        )

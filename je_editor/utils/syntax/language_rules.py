"""
各語言的語法高亮規則
The highlighting rules for each language.

Python 已經有專屬的高亮器；這裡放的是其他語言的規則，讓打開 TypeScript、Rust、
Go 這類檔案時不再是一片白。
Python already has a highlighter of its own; these are the rules for everything
else, so opening a TypeScript, Rust or Go file is no longer a wall of plain text.

純資料：不含 Qt，因此規則本身可以單獨測試。
Pure data with no Qt, so the rules themselves can be tested on their own.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 幾乎每個 C 家族語言都共用的關鍵字 / Keywords shared across the C-family languages
_COMMON = (
    "if", "else", "for", "while", "return", "break", "continue", "switch",
    "case", "default", "do", "goto", "struct", "enum", "union", "const",
    "static", "void", "int", "char", "long", "short", "float", "double",
    "unsigned", "signed", "sizeof", "typedef",
)


@dataclass(frozen=True)
class LanguageRules:
    """
    一個語言的高亮規則
    The highlighting rules for one language.

    :param name: 語言名稱 / the language's name
    :param keywords: 關鍵字 / its keywords
    :param line_comment: 單行註解的開頭 / what starts a line comment
    :param block_comment: 區塊註解的起訖，沒有就是 ``None``
        the delimiters of a block comment, or ``None`` when it has none
    :param string_delimiters: 字串的引號 / the quote characters for strings
    """

    name: str
    keywords: tuple[str, ...]
    line_comment: str = "//"
    block_comment: tuple[str, str] | None = ("/*", "*/")
    string_delimiters: tuple[str, ...] = field(default=('"', "'"))


# 副檔名對應的規則 / The rules for each file suffix
LANGUAGE_RULES: dict[str, LanguageRules] = {
    ".js": LanguageRules("JavaScript", (
        "function", "var", "let", "const", "class", "extends", "new", "this",
        "return", "if", "else", "for", "while", "of", "in", "try", "catch",
        "finally", "throw", "typeof", "instanceof", "async", "await", "import",
        "export", "from", "default", "null", "undefined", "true", "false",
    ), string_delimiters=('"', "'", "`")),
    ".ts": LanguageRules("TypeScript", (
        "function", "var", "let", "const", "class", "interface", "type", "enum",
        "extends", "implements", "new", "this", "return", "if", "else", "for",
        "while", "of", "in", "try", "catch", "finally", "throw", "typeof",
        "async", "await", "import", "export", "from", "default", "public",
        "private", "protected", "readonly", "as", "null", "undefined",
        "true", "false", "string", "number", "boolean", "any", "void",
    ), string_delimiters=('"', "'", "`")),
    ".rs": LanguageRules("Rust", (
        "fn", "let", "mut", "const", "struct", "enum", "impl", "trait", "pub",
        "use", "mod", "match", "if", "else", "loop", "while", "for", "in",
        "return", "self", "Self", "where", "async", "await", "move", "ref",
        "dyn", "unsafe", "true", "false", "Some", "None", "Ok", "Err",
    )),
    ".go": LanguageRules("Go", (
        "func", "var", "const", "type", "struct", "interface", "map", "chan",
        "package", "import", "return", "if", "else", "for", "range", "switch",
        "case", "default", "go", "defer", "select", "nil", "true", "false",
        "string", "int", "error",
    ), string_delimiters=('"', "`")),
    ".c": LanguageRules("C", _COMMON),
    ".h": LanguageRules("C header", _COMMON),
    ".cpp": LanguageRules("C++", _COMMON + (
        "class", "public", "private", "protected", "virtual", "template",
        "namespace", "using", "new", "delete", "this", "nullptr", "auto",
        "override", "constexpr", "true", "false",
    )),
    ".hpp": LanguageRules("C++ header", _COMMON + (
        "class", "public", "private", "protected", "virtual", "template",
        "namespace", "using", "nullptr", "auto", "true", "false",
    )),
    ".java": LanguageRules("Java", (
        "class", "interface", "extends", "implements", "public", "private",
        "protected", "static", "final", "void", "new", "this", "super",
        "return", "if", "else", "for", "while", "switch", "case", "try",
        "catch", "finally", "throw", "throws", "import", "package", "null",
        "true", "false", "int", "long", "double", "boolean", "String",
    )),
    ".sh": LanguageRules("Shell", (
        "if", "then", "else", "elif", "fi", "for", "while", "do", "done",
        "case", "esac", "function", "return", "export", "local", "echo",
    ), line_comment="#", block_comment=None),
    ".yaml": LanguageRules("YAML", ("true", "false", "null"),
                           line_comment="#", block_comment=None),
    ".yml": LanguageRules("YAML", ("true", "false", "null"),
                          line_comment="#", block_comment=None),
    ".toml": LanguageRules("TOML", ("true", "false"),
                           line_comment="#", block_comment=None),
    ".json": LanguageRules("JSON", ("true", "false", "null"),
                           line_comment="//", block_comment=None,
                           string_delimiters=('"',)),
    ".sql": LanguageRules("SQL", (
        "select", "from", "where", "insert", "into", "values", "update", "set",
        "delete", "create", "table", "drop", "alter", "join", "left", "right",
        "inner", "outer", "on", "group", "order", "by", "having", "limit",
        "and", "or", "not", "null", "as", "distinct",
    ), line_comment="--", block_comment=("/*", "*/")),
}


def rules_for(suffix: str) -> LanguageRules | None:
    """
    取得副檔名對應的高亮規則
    The highlighting rules for a file suffix.

    Python 不在其中，因為它有專屬的高亮器。
    Python is absent, since it has a highlighter of its own.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 規則，沒有對應時為 ``None`` / the rules, or ``None``
    """
    return LANGUAGE_RULES.get(suffix.lower())


def supported_suffixes() -> tuple[str, ...]:
    """
    取得所有支援的副檔名
    Every suffix that has rules.

    :return: 副檔名 / the suffixes
    """
    return tuple(sorted(LANGUAGE_RULES))

"""
識別字命名風格轉換（純邏輯，不含 Qt）
Identifier naming-style conversion (pure logic, no Qt imports).

支援 snake_case、camelCase、PascalCase 與 kebab-case 互轉。先把輸入切成一個個
「詞」，再依目標風格重新組合。
Converts between snake_case, camelCase, PascalCase and kebab-case. The input is
first split into words, then recombined in the target style.
"""
from __future__ import annotations

import re

# 分隔符號：底線、連字號、空白 / Separators: underscore, hyphen, whitespace
_SEPARATOR_RE = re.compile(r"[_\-\s]+")
# 小寫或數字之後接大寫：詞界 / lower/digit followed by upper: a word boundary
_LOWER_UPPER_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
# 連續大寫之後接「大寫+小寫」：縮寫與後續詞的界線（HTTPServer -> HTTP Server）
# A run of capitals before an upper+lower: acronym/word boundary (HTTPServer -> HTTP Server)
_ACRONYM_RE = re.compile(r"(?<=[A-Z])(?=[A-Z][a-z])")


def split_words(text: str) -> list[str]:
    """
    把識別字切成一個個詞
    Split an identifier into its component words.

    同時處理底線、連字號、空白，以及 camelCase / PascalCase 的大小寫邊界，
    並保留縮寫（例如 ``parseHTTPResponse`` → ``parse``, ``HTTP``, ``Response``）。
    Handles underscores, hyphens, whitespace and camelCase / PascalCase boundaries,
    keeping acronyms intact (e.g. ``parseHTTPResponse`` -> ``parse``, ``HTTP``,
    ``Response``).

    :param text: 要拆解的識別字 / The identifier to split
    :return: 詞的清單（皆為非空字串）/ The list of words (all non-empty)
    """
    spaced = _SEPARATOR_RE.sub(" ", text)
    spaced = _ACRONYM_RE.sub(" ", spaced)
    spaced = _LOWER_UPPER_RE.sub(" ", spaced)
    return [word for word in spaced.split(" ") if word]


def to_snake_case(text: str) -> str:
    """轉為 ``snake_case`` / Convert to ``snake_case``."""
    return "_".join(word.lower() for word in split_words(text))


def to_kebab_case(text: str) -> str:
    """轉為 ``kebab-case`` / Convert to ``kebab-case``."""
    return "-".join(word.lower() for word in split_words(text))


def to_camel_case(text: str) -> str:
    """轉為 ``camelCase`` / Convert to ``camelCase``."""
    words = split_words(text)
    if not words:
        return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])


def to_pascal_case(text: str) -> str:
    """轉為 ``PascalCase`` / Convert to ``PascalCase``."""
    return "".join(word.capitalize() for word in split_words(text))

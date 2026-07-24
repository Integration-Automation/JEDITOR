"""
文字統計（純邏輯，不含 Qt）
Text statistics (pure logic, no Qt imports).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# 以連續的非空白字元視為一個「詞」/ A run of non-whitespace counts as one word
_WORD_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class TextStatistics:
    """
    一段文字的統計數據
    Statistics for a piece of text.

    :param lines: 行數 / Number of lines
    :param words: 詞數（以空白分隔）/ Number of words (whitespace separated)
    :param characters: 字元數（含空白）/ Number of characters (including whitespace)
    :param characters_no_spaces: 不含空白的字元數 / Characters excluding whitespace
    """

    lines: int
    words: int
    characters: int
    characters_no_spaces: int


def text_statistics(text: str) -> TextStatistics:
    """
    計算一段文字的行數、詞數與字元數
    Compute line, word and character counts for a piece of text.

    空字串視為 0 行；非空文字至少有 1 行。字元數以 Unicode 字元（``len``）計算，
    因此表情符號等各算一個字元。
    An empty string is 0 lines; non-empty text has at least one line. Characters are
    counted as Unicode code points (``len``), so an emoji counts as one character.

    :param text: 要統計的文字 / The text to measure
    :return: 統計結果 / The statistics
    """
    characters = len(text)
    characters_no_spaces = sum(1 for char in text if not char.isspace())
    words = len(_WORD_RE.findall(text))
    lines = 0 if text == "" else text.count("\n") + 1
    return TextStatistics(
        lines=lines,
        words=words,
        characters=characters,
        characters_no_spaces=characters_no_spaces,
    )

"""
找出游標所在字詞與其所有出現位置（純邏輯，不含 Qt）
Find the word under the caret and all its occurrences (pure logic, no Qt imports).
"""
from __future__ import annotations

import keyword
import re

# 出現次數高亮的最短字詞長度，避免單字元造成滿畫面雜訊
# Minimum word length for occurrence highlighting, to avoid single-char noise
MIN_WORD_LENGTH = 2


def _is_identifier_char(char: str) -> bool:
    """判斷字元是否可構成識別字 / Whether a char can be part of an identifier."""
    return char.isalnum() or char == "_"


def word_at(text: str, position: int) -> tuple[str, int, int] | None:
    """
    取得指定位置的識別字
    Return the identifier at a character position.

    位置可以落在字詞內或字詞的右緣（游標在字尾後方），兩者都會回傳該字詞。
    The position may sit inside the word or just past its right edge (caret after
    the last char); both return the word.

    :param text: 完整文字 / The full text
    :param position: 字元位置（0 起算）/ The character position (0-based)
    :return: ``(word, start, end)``，不在識別字上時回傳 ``None``
        / ``(word, start, end)``, or ``None`` when not on an identifier
    """
    if position < 0 or position > len(text):
        return None
    start = position
    while start > 0 and _is_identifier_char(text[start - 1]):
        start -= 1
    end = position
    while end < len(text) and _is_identifier_char(text[end]):
        end += 1
    if start == end:
        return None
    return text[start:end], start, end


def is_highlightable_word(word: str) -> bool:
    """
    判斷字詞是否值得做出現次數高亮
    Whether a word is worth highlighting occurrences of.

    排除過短的字詞、非識別字與 Python 關鍵字（如 ``if``、``def``），避免雜訊。
    Excludes short words, non-identifiers and Python keywords (``if``, ``def``, …)
    to keep the highlight meaningful.

    :param word: 要檢查的字詞 / The word to check
    :return: 值得高亮時為 ``True`` / ``True`` when worth highlighting
    """
    return (
        len(word) >= MIN_WORD_LENGTH
        and word.isidentifier()
        and not keyword.iskeyword(word)
    )


def replace_whole_word(text: str, word: str, replacement: str) -> str:
    """
    以完整字界把文字中所有的 ``word`` 換成 ``replacement``
    Replace every whole-word occurrence of ``word`` with ``replacement``.

    以字界（``\\b``）比對，因此 ``value`` 不會動到 ``values`` 或 ``old_value``。
    取代字串以字面值插入，內含的反斜線不會被當成正規表示式的參照。
    Matching uses word boundaries, so ``value`` never touches ``values`` or
    ``old_value``. The replacement is inserted literally; backslashes in it are not
    treated as regex backreferences.

    :param text: 原始文字 / The original text
    :param word: 要被取代的字詞（需為合法識別字）/ The word to replace (must be an identifier)
    :param replacement: 取代成的字詞 / The replacement word
    :return: 取代後的文字；``word`` 非識別字時原樣回傳 / The new text, unchanged when ``word`` is not an identifier
    """
    if not word.isidentifier():
        return text
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    return pattern.sub(lambda _match: replacement, text)


def lines_containing(text: str, term: str, case_sensitive: bool = False) -> list[int]:
    """
    找出含有指定字串的行
    Find the lines that contain a piece of text.

    這是「搜尋框正在找的東西」用的：比對的是使用者輸入的字串本身，不加字界也不
    要求是識別字，因此 ``val`` 會在 ``value`` 裡命中——搜尋本來就該如此。
    This backs what the search box is looking for: it matches the string the user
    typed, with no word boundaries and no identifier requirement, so ``val`` does
    hit inside ``value`` — which is what searching is meant to do.

    :param text: 要搜尋的文字 / the text to search
    :param term: 要尋找的字串 / the string to find
    :param case_sensitive: 是否區分大小寫 / whether case matters
    :return: 含有該字串的行號（0 起算，已排序去重）
        / the 0-based line numbers holding it, sorted and unique
    """
    if not term:
        return []
    needle = term if case_sensitive else term.lower()
    return [
        number for number, line in enumerate(text.splitlines())
        if needle in (line if case_sensitive else line.lower())
    ]


def find_occurrences(text: str, word: str) -> list[int]:
    """
    找出字詞在文字中所有以完整字界出現的位置
    Find every whole-word occurrence of ``word`` in ``text``.

    以字界（``\\b``）比對，因此 ``value`` 不會匹配到 ``values`` 或 ``old_value``。
    Matching uses word boundaries, so ``value`` never matches ``values`` or
    ``old_value``.

    :param text: 要搜尋的文字 / The text to search
    :param word: 要尋找的字詞 / The word to find
    :return: 每個出現的起始位置 / The start position of each occurrence
    """
    if not is_highlightable_word(word):
        return []
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    return [match.start() for match in pattern.finditer(text)]

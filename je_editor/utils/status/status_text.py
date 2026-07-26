"""
組出狀態列要顯示的文字
Build the text the status bar shows.

純邏輯，不匯入 Qt，因此可以單獨測試；狀態列本身只負責把這些字串放上去。
Pure logic with no Qt import so it can be tested on its own; the status bar
itself only has to put these strings on screen.
"""
from __future__ import annotations

from pathlib import Path

from je_editor.utils.encodings.text_codec import DEFAULT_ENCODING, line_ending_name
from je_editor.utils.syntax.language_rules import rules_for

# Python 有專屬的高亮器，因此不在通用規則表中
# Python has a highlighter of its own and so is absent from the generic rules
_PYTHON_SUFFIXES = (".py", ".pyi", ".pyw")
# 沒有對應語言時顯示的名稱 / Shown when no language is recognised
PLAIN_TEXT = "Plain Text"


def language_name(file_path: str | Path | None) -> str:
    """
    取得檔案對應的語言名稱
    The language name for a file.

    :param file_path: 檔案路徑，未存檔時為 ``None`` / the file, or ``None`` when unsaved
    :return: 語言名稱，認不出來時為 ``Plain Text`` / the name, or ``Plain Text``
    """
    if file_path is None:
        return PLAIN_TEXT
    suffix = Path(str(file_path)).suffix.lower()
    if suffix in _PYTHON_SUFFIXES:
        return "Python"
    rules = rules_for(suffix)
    return rules.name if rules is not None else PLAIN_TEXT


def encoding_name(encoding: str | None) -> str:
    """
    取得編碼的顯示名稱
    The display name of an encoding.

    :param encoding: 編碼名稱 / the encoding
    :return: 大寫的名稱 / the name in upper case
    """
    return (encoding or DEFAULT_ENCODING).upper()


def line_ending_display(ending: str | None) -> str:
    """
    取得行尾的顯示名稱
    The display name of a line ending.

    :param ending: 行尾字串 / the line-ending string
    :return: ``CRLF``、``LF`` 或 ``CR`` / one of ``CRLF``, ``LF`` or ``CR``
    """
    return line_ending_name(ending or "\n")


def cursor_position(line: int, column: int) -> str:
    """
    取得游標位置的顯示文字
    The display text for a caret position.

    :param line: 以 1 起算的行號 / the 1-based line number
    :param column: 以 1 起算的欄號 / the 1-based column number
    :return: 顯示文字 / the text to show
    """
    return f"Ln {max(1, line)}, Col {max(1, column)}"

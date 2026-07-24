"""
文字清理轉換（純邏輯，不含 Qt）
Whitespace cleanup transforms (pure logic, no Qt imports).
"""
from __future__ import annotations

# 分行用的換行字元；編輯器內部一律使用 "\n" / Newline used to split lines
_NEWLINE = "\n"


def trim_trailing_whitespace(text: str) -> str:
    """
    移除每一行結尾的空白
    Strip trailing whitespace from every line.

    只處理行尾空白，行數與行的內容順序都不變，因此對游標與折疊等狀態影響最小。
    Only trailing whitespace is touched; the number of lines and their order are
    preserved, keeping the impact on caret and folding state minimal.

    :param text: 原始文字 / The original text
    :return: 每行去除行尾空白後的文字 / Text with per-line trailing whitespace removed
    """
    return _NEWLINE.join(line.rstrip() for line in text.split(_NEWLINE))


def ensure_final_newline(text: str) -> str:
    """
    確保非空文字以換行結尾
    Ensure non-empty text ends with a newline.

    空字串維持原樣，避免在空檔案裡憑空加入一行。
    An empty string is left as-is, so an empty file gains no phantom line.

    :param text: 原始文字 / The original text
    :return: 結尾補上換行的文字 / Text ending with a newline
    """
    if not text or text.endswith(_NEWLINE):
        return text
    return text + _NEWLINE


def strip_trailing_blank_lines(text: str) -> str:
    """
    移除檔案結尾多餘的空白行
    Remove blank lines at the end of the file.

    保留最後一行的實際內容，並移除其後所有空白行；不會在結尾補上換行。
    Keeps the last non-blank line and drops every blank line after it; it does not
    add a trailing newline.

    :param text: 原始文字 / The original text
    :return: 去除結尾空白行後的文字 / Text with trailing blank lines removed
    """
    lines = text.split(_NEWLINE)
    while len(lines) > 1 and lines[-1].strip() == "":
        lines.pop()
    return _NEWLINE.join(lines)

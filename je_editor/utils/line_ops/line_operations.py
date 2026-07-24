"""
行操作的純文字轉換（純邏輯，不含 Qt）
Pure text transforms for line operations (pure logic, no Qt imports).

這些函式只做「文字進、文字出」的轉換，Qt 層負責把結果套用回編輯器並維持選取。
These functions are pure text-in/text-out transforms; the Qt layer applies the
result back to the editor and keeps the selection.
"""
from __future__ import annotations

import re

# 把字串切成「數字」與「非數字」片段，供自然排序使用
# Split a string into digit / non-digit chunks for natural sorting
_NATURAL_CHUNK_RE = re.compile(r"(\d+)")


def sort_lines(lines: list[str], reverse: bool = False, case_sensitive: bool = True) -> list[str]:
    """
    排序多行文字
    Sort a list of lines.

    :param lines: 要排序的行 / The lines to sort
    :param reverse: 是否遞減排序 / Whether to sort in descending order
    :param case_sensitive: 是否區分大小寫 / Whether the sort is case-sensitive
    :return: 排序後的新清單 / A new sorted list
    """
    key = None if case_sensitive else str.casefold
    return sorted(lines, key=key, reverse=reverse)


def unique_lines(lines: list[str]) -> list[str]:
    """
    移除重複行並保留首次出現的順序
    Remove duplicate lines, keeping the first occurrence's order.

    :param lines: 要處理的行 / The lines to process
    :return: 去除重複後的新清單 / A new list with duplicates removed
    """
    seen: set[str] = set()
    result: list[str] = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            result.append(line)
    return result


def natural_sort_key(line: str) -> list:
    """
    產生自然排序用的鍵值
    Build a key for natural (human-friendly) sorting.

    數字片段以數值比較，因此 ``item2`` 會排在 ``item10`` 前面。
    Digit runs are compared numerically, so ``item2`` sorts before ``item10``.

    :param line: 要產生鍵值的字串 / The string to key
    :return: 供 ``sorted`` 使用的比較鍵 / A comparison key for ``sorted``
    """
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in _NATURAL_CHUNK_RE.split(line)
    ]


def natural_sort(lines: list[str]) -> list[str]:
    """
    以自然順序排序多行文字
    Sort lines in natural (human-friendly) order.

    :param lines: 要排序的行 / The lines to sort
    :return: 排序後的新清單 / A new sorted list
    """
    return sorted(lines, key=natural_sort_key)


def remove_blank_lines(lines: list[str]) -> list[str]:
    """
    移除只有空白（或完全空）的行
    Remove lines that are blank or contain only whitespace.

    :param lines: 要處理的行 / The lines to process
    :return: 去除空白行後的新清單 / A new list without blank lines
    """
    return [line for line in lines if line.strip() != ""]


def reverse_lines(lines: list[str]) -> list[str]:
    """
    反轉多行的順序
    Reverse the order of the lines.

    :param lines: 要反轉的行 / The lines to reverse
    :return: 反轉後的新清單 / A new list in reversed order
    """
    return list(reversed(lines))


def join_lines(lines: list[str], separator: str = " ") -> str:
    """
    把多行併成一行
    Join several lines into a single line.

    每行會先去除前後空白，避免併行後出現多餘空格；以 ``separator`` 連接。
    Each line is stripped first so no stray whitespace remains, then joined with
    ``separator``.

    :param lines: 要併接的行 / The lines to join
    :param separator: 連接字串 / The string placed between lines
    :return: 併接後的單行 / The single joined line
    """
    non_empty = [line.strip() for line in lines if line.strip() != ""]
    return separator.join(non_empty)


def delete_line(lines: list[str], index: int) -> list[str]:
    """
    刪除指定索引的行
    Delete the line at ``index``.

    索引超出範圍時回傳原內容的複本，避免呼叫端需要另外檢查。
    An out-of-range index returns a copy of the input, so callers need no guard.

    :param lines: 原始行 / The original lines
    :param index: 要刪除的行索引（0 起算）/ The 0-based line index to delete
    :return: 刪除後的新清單 / A new list with the line removed
    """
    if index < 0 or index >= len(lines):
        return list(lines)
    return lines[:index] + lines[index + 1:]

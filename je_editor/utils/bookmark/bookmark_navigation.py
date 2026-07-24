"""
書籤導覽邏輯（純邏輯，不含 Qt）
Bookmark navigation logic (pure logic, no Qt imports).

只處理「從目前行往下 / 往上找到哪個書籤」，實際移動游標留給 UI 層。
Only decides which bookmark comes next / previous from the current line; the UI
layer performs the actual cursor move.
"""
from __future__ import annotations

from typing import Iterable


def normalise_lines(lines: Iterable[int]) -> list[int]:
    """
    去除重複並排序書籤行號
    Deduplicate and sort bookmark line numbers.

    :param lines: 書籤行號 / Bookmark line numbers
    :return: 由小到大排序、無重複的行號 / Sorted, unique line numbers
    """
    return sorted(set(lines))


def next_bookmark(lines: Iterable[int], current: int, wrap: bool = True) -> int | None:
    """
    找到目前行之後的下一個書籤
    Find the first bookmark after the current line.

    :param lines: 書籤行號 / Bookmark line numbers
    :param current: 目前所在行 / The current line
    :param wrap: 找不到時是否從頭繞回 / Whether to wrap to the first bookmark
    :return: 下一個書籤行，沒有書籤時回傳 ``None``
        / The next bookmark line, or ``None`` when there are no bookmarks
    """
    ordered = normalise_lines(lines)
    if not ordered:
        return None
    for line in ordered:
        if line > current:
            return line
    return ordered[0] if wrap else None


def prev_bookmark(lines: Iterable[int], current: int, wrap: bool = True) -> int | None:
    """
    找到目前行之前的上一個書籤
    Find the last bookmark before the current line.

    :param lines: 書籤行號 / Bookmark line numbers
    :param current: 目前所在行 / The current line
    :param wrap: 找不到時是否從尾端繞回 / Whether to wrap to the last bookmark
    :return: 上一個書籤行，沒有書籤時回傳 ``None``
        / The previous bookmark line, or ``None`` when there are no bookmarks
    """
    ordered = normalise_lines(lines)
    if not ordered:
        return None
    for line in reversed(ordered):
        if line < current:
            return line
    return ordered[-1] if wrap else None


def toggle_line(lines: Iterable[int], line: int) -> list[int]:
    """
    切換某一行的書籤狀態
    Toggle the bookmark state of one line.

    :param lines: 現有書籤行號 / Existing bookmark line numbers
    :param line: 要切換的行 / The line to toggle
    :return: 切換後排序的行號清單 / The resulting sorted line numbers
    """
    current = set(normalise_lines(lines))
    if line in current:
        current.discard(line)
    else:
        current.add(line)
    return sorted(current)

"""
管理一個編輯器的中斷點
Track the breakpoints set in one editor.

中斷點跟著文字走：在上方插入或刪除行時，標記要跟著移動，否則加一行就會讓每個
中斷點都指到錯的地方。書籤已經用 ``QTextCursor`` 解決過同樣的問題，這裡沿用。
Breakpoints follow the text: inserting or removing a line above one has to move
it, or adding a line would leave every breakpoint pointing at the wrong place.
Bookmarks already solve this with ``QTextCursor``, and the same approach is used
here.
"""
from __future__ import annotations

from PySide6.QtGui import QTextCursor


class BreakpointManager:
    """
    追蹤中斷點所在的行
    Track which lines have a breakpoint.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 這些中斷點所屬的編輯器 / the editor they belong to
        """
        self._code_edit = code_edit
        self._cursors: list[QTextCursor] = []

    def lines(self) -> list[int]:
        """
        取得目前有中斷點的行（0 起算，已排序）
        The lines that currently have a breakpoint, 0-based and sorted.

        :return: 行號 / the line numbers
        """
        return sorted({cursor.blockNumber() for cursor in self._cursors})

    def has_breakpoint(self, line: int) -> bool:
        """
        判斷某行是否有中斷點
        Whether a line has a breakpoint.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 有的話為 ``True`` / ``True`` when it has one
        """
        return line in self.lines()

    def toggle(self, line: int) -> bool:
        """
        切換某一行的中斷點
        Add or remove the breakpoint on a line.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 切換後是否有中斷點 / whether the line now has one
        """
        for cursor in list(self._cursors):
            if cursor.blockNumber() == line:
                self._cursors.remove(cursor)
                return False
        block = self._code_edit.document().findBlockByNumber(line)
        if not block.isValid():
            return False
        cursor = QTextCursor(block)
        self._cursors.append(cursor)
        return True

    def clear(self) -> bool:
        """
        清除所有中斷點
        Remove every breakpoint.

        :return: 是否真的清掉了什麼 / whether anything was removed
        """
        if not self._cursors:
            return False
        self._cursors = []
        return True

    def pdb_lines(self) -> list[int]:
        """
        取得給 pdb 用的行號（1 起算）
        The line numbers as pdb counts them, from one.

        :return: 行號 / the line numbers
        """
        return [line + 1 for line in self.lines()]

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
        # 跟 _cursors 一一對應：每個中斷點的條件，空字串表示一律停
        # In step with _cursors: each breakpoint's condition, empty to stop every time
        self._conditions: list[str] = []

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
        existing = next(
            (cursor for cursor in self._cursors if cursor.blockNumber() == line), None)
        if existing is not None:
            index = self._cursors.index(existing)
            del self._cursors[index]
            del self._conditions[index]
            return False
        block = self._code_edit.document().findBlockByNumber(line)
        if not block.isValid():
            return False
        cursor = QTextCursor(block)
        self._cursors.append(cursor)
        self._conditions.append("")
        return True

    def condition(self, line: int) -> str:
        """
        取得某一行中斷點的條件
        The condition of the breakpoint on a line.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 條件；那一行沒有中斷點或沒有條件時為空字串
            the condition, empty when the line has no breakpoint or no condition
        """
        return dict(self.breakpoints()).get(line, "")

    def set_condition(self, line: int, condition: str) -> bool:
        """
        設定某一行中斷點的條件；那一行沒有中斷點時先加上
        Set the condition of the breakpoint on a line, adding the breakpoint first when there is none.

        :param line: 以 0 起算的行號 / the 0-based line number
        :param condition: 成立才停下來的條件，空字串表示一律停
            the condition that has to hold to stop, empty to stop every time
        :return: 那一行現在有中斷點時為 ``True`` / ``True`` when the line now has a breakpoint
        """
        if not self.has_breakpoint(line) and not self.toggle(line):
            return False
        for index, cursor in enumerate(self._cursors):
            if cursor.blockNumber() == line:
                self._conditions[index] = condition
        return True

    def breakpoints(self) -> list[tuple[int, str]]:
        """
        取得每個中斷點的行號與條件
        Every breakpoint's line and condition.

        編輯可能讓兩個中斷點落在同一行，這時只留先設的那一個。
        Editing can bring two breakpoints onto one line, and then the one set first is kept.

        :return: ``(以 0 起算的行號, 條件)``，依行號排序 / ``(0-based line, condition)``, sorted by line
        """
        found: dict[int, str] = {}
        for cursor, condition in zip(self._cursors, self._conditions):
            found.setdefault(cursor.blockNumber(), condition)
        return sorted(found.items())

    def clear(self) -> bool:
        """
        清除所有中斷點
        Remove every breakpoint.

        :return: 是否真的清掉了什麼 / whether anything was removed
        """
        if not self._cursors:
            return False
        self._cursors = []
        self._conditions = []
        return True

    def pdb_lines(self) -> list[int]:
        """
        取得給 pdb 用的行號（1 起算）
        The line numbers as pdb counts them, from one.

        :return: 行號 / the line numbers
        """
        return [line + 1 for line in self.lines()]

"""
書籤管理器（Qt 整合層）
Bookmark manager (Qt integration layer).

每個書籤以 ``QTextCursor`` 錨定在該行開頭。當上方插入或刪除文字時，
``QTextCursor`` 會自動跟著移動，因此書籤能正確地跟著程式碼移動而不會漂移。
Each bookmark is anchored by a ``QTextCursor`` at the line start. A ``QTextCursor``
moves automatically when text is inserted or removed above it, so bookmarks follow
the code they mark instead of drifting.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QTextCursor

from je_editor.utils.bookmark.bookmark_navigation import next_bookmark, prev_bookmark

if TYPE_CHECKING:
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor


class BookmarkManager:
    """
    管理單一編輯器的書籤
    Manage the bookmarks of one editor.
    """

    def __init__(self, editor: CodeEditor) -> None:
        """
        :param editor: 被管理的程式碼編輯器 / The code editor being managed
        """
        self._editor = editor
        self._cursors: list[QTextCursor] = []

    def bookmarked_lines(self) -> list[int]:
        """
        取得目前所有書籤的行號
        Return the current bookmark line numbers.

        每次即時查詢游標的行號，因此反映文字編輯後的最新位置。
        The line is read from each cursor live, so it reflects edits made since.

        :return: 由小到大排序、無重複的行號（0 起算）/ Sorted, unique 0-based line numbers
        """
        return sorted({cursor.blockNumber() for cursor in self._cursors})

    def is_bookmarked(self, line: int) -> bool:
        """
        判斷某一行是否有書籤
        Return whether a line is bookmarked.

        :param line: 行號（0 起算）/ The line (0-based)
        :return: 有書籤時為 ``True`` / ``True`` when bookmarked
        """
        return any(cursor.blockNumber() == line for cursor in self._cursors)

    def toggle(self, line: int) -> bool:
        """
        切換某一行的書籤
        Toggle the bookmark on a line.

        :param line: 行號（0 起算）/ The line (0-based)
        :return: 切換後該行有書籤時為 ``True`` / ``True`` when the line ends up bookmarked
        """
        existing = [cursor for cursor in self._cursors if cursor.blockNumber() == line]
        if existing:
            self._cursors = [cursor for cursor in self._cursors if cursor.blockNumber() != line]
            return False
        cursor = self._cursor_at_line(line)
        if cursor is None:
            return False
        self._cursors.append(cursor)
        return True

    def toggle_current(self) -> bool:
        """
        切換游標所在行的書籤
        Toggle the bookmark on the line holding the caret.

        :return: 切換後該行有書籤時為 ``True`` / ``True`` when the line ends up bookmarked
        """
        return self.toggle(self._editor.textCursor().blockNumber())

    def clear(self) -> None:
        """清除所有書籤 / Remove every bookmark."""
        self._cursors.clear()

    def go_to_next(self, wrap: bool = True) -> int | None:
        """
        跳到下一個書籤
        Jump to the next bookmark.

        :param wrap: 找不到時是否從頭繞回 / Whether to wrap to the first bookmark
        :return: 跳到的行號，沒有書籤時回傳 ``None`` / The line jumped to, or ``None``
        """
        target = next_bookmark(
            self.bookmarked_lines(), self._editor.textCursor().blockNumber(), wrap)
        return self._jump_to(target)

    def go_to_previous(self, wrap: bool = True) -> int | None:
        """
        跳到上一個書籤
        Jump to the previous bookmark.

        :param wrap: 找不到時是否從尾端繞回 / Whether to wrap to the last bookmark
        :return: 跳到的行號，沒有書籤時回傳 ``None`` / The line jumped to, or ``None``
        """
        target = prev_bookmark(
            self.bookmarked_lines(), self._editor.textCursor().blockNumber(), wrap)
        return self._jump_to(target)

    def _cursor_at_line(self, line: int):
        """建立錨定在指定行開頭的游標 / Build a cursor anchored at a line's start."""
        block = self._editor.document().findBlockByNumber(line)
        if not block.isValid():
            return None
        cursor = QTextCursor(block)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        return cursor

    def _jump_to(self, line: int | None) -> int | None:
        """把編輯器游標移到指定行 / Move the editor caret to a line."""
        if line is None:
            return None
        block = self._editor.document().findBlockByNumber(line)
        if not block.isValid():
            return None
        cursor = self._editor.textCursor()
        cursor.setPosition(block.position())
        self._editor.setTextCursor(cursor)
        self._editor.centerCursor()
        self._editor.highlight_current_line()
        return line

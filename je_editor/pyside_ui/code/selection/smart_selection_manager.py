"""
智慧選取管理器（Qt 整合層）
Smart selection manager (Qt integration layer).

負責把純邏輯算出的範圍套用到編輯器，並維護一個「縮回」用的堆疊。
Applies the ranges computed by the pure logic to the editor and keeps a stack so
selections can be shrunk back to their previous size.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QTextCursor

from je_editor.utils.selection.smart_selection import expand_selection

if TYPE_CHECKING:
    from je_editor.pyside_ui.code.plaintext_code_edit.code_edit_plaintext import CodeEditor


class SmartSelectionManager:
    """
    管理單一編輯器的智慧選取擴大 / 縮回
    Manage smart selection expand/shrink for one editor.

    使用者手動改變選取時堆疊會失效，因此「縮回」永遠只會回到由「擴大」建立的範圍。
    The stack is invalidated when the user changes the selection manually, so shrink
    only ever returns to ranges that expand itself created.
    """

    def __init__(self, editor: CodeEditor) -> None:
        """
        :param editor: 被管理的程式碼編輯器 / The code editor being managed
        """
        self._editor = editor
        self._stack: list[tuple[int, int]] = []
        self._last_applied: tuple[int, int] | None = None

    def _current_range(self) -> tuple[int, int]:
        """目前選取的字元範圍 / The current selection's character range."""
        cursor = self._editor.textCursor()
        return cursor.selectionStart(), cursor.selectionEnd()

    def _sync_stack_with_selection(self, current: tuple[int, int]) -> None:
        """選取被使用者改動時清空堆疊 / Clear the stack when the user changed the selection."""
        if self._last_applied is not None and current != self._last_applied:
            self._stack.clear()

    def expand(self) -> bool:
        """
        把選取擴大到下一個更大的範圍
        Expand the selection to the next larger range.

        :return: 有擴大時為 ``True`` / ``True`` when the selection grew
        """
        text = self._editor.toPlainText()
        start, end = self._current_range()
        self._sync_stack_with_selection((start, end))
        new_range = expand_selection(text, start, end)
        if new_range is None:
            return False
        self._stack.append((start, end))
        self._apply(new_range)
        return True

    def shrink(self) -> bool:
        """
        縮回上一個較小的範圍
        Shrink back to the previous smaller range.

        :return: 有縮回時為 ``True`` / ``True`` when the selection shrank
        """
        current = self._current_range()
        self._sync_stack_with_selection(current)
        if not self._stack:
            return False
        self._apply(self._stack.pop())
        return True

    def _apply(self, selection_range: tuple[int, int]) -> None:
        """把字元範圍套用成編輯器選取 / Apply a character range as the editor selection."""
        start, end = selection_range
        cursor = self._editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        self._editor.setTextCursor(cursor)
        self._last_applied = selection_range

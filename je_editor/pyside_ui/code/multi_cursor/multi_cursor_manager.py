"""
在編輯器中維護並套用多重游標
Keep and apply extra carets in the editor.

QPlainTextEdit 只有一個游標，所以額外的游標由這裡自己記錄位置、自己畫出來，
輸入與刪除時再逐一套用；整批編輯算一個復原步驟。
QPlainTextEdit has only one caret, so the extra ones are tracked and drawn here
and each edit is applied to every position in turn, as a single undo step.
"""
from __future__ import annotations

from PySide6.QtGui import QTextCursor

from je_editor.utils.multi_cursor.cursor_positions import clamp_positions, toggle_position


class MultiCursorManager:
    """
    管理一個編輯器的額外游標
    Track one editor's extra carets.
    """

    def __init__(self, code_edit) -> None:
        """
        :param code_edit: 這些游標所屬的編輯器 / the editor the carets belong to
        """
        self._code_edit = code_edit
        self._positions: list[int] = []

    @property
    def active(self) -> bool:
        """是否有額外游標 / Whether any extra caret exists."""
        return bool(self._positions)

    def positions(self) -> list[int]:
        """取得額外游標的位置副本 / A copy of the extra caret positions."""
        return list(self._positions)

    def clear(self) -> bool:
        """
        清除所有額外游標
        Drop every extra caret.

        :return: 是否真的清掉了什麼 / whether anything was actually dropped
        """
        if not self._positions:
            return False
        self._positions = []
        self._code_edit.viewport().update()
        return True

    def toggle_at(self, position: int) -> None:
        """
        在指定位置加入或移除一個游標
        Add or remove a caret at a position.

        :param position: 文件中的字元位置 / a character position in the document
        """
        self._positions = toggle_position(self._positions, position)
        self._code_edit.viewport().update()

    def add_to_selected_lines(self) -> int:
        """
        在選取範圍的每一行加入游標
        Put a caret on every line of the selection.

        游標放在各行的行尾，這是逐行改結尾（例如補上逗號）最常用的形式。
        Each caret goes to its line's end, which is the form most used for
        editing line by line — appending a comma to each, say.

        :return: 加入的游標數量 / how many carets were added
        """
        cursor = self._code_edit.textCursor()
        if not cursor.hasSelection():
            return 0
        document = self._code_edit.document()
        first = document.findBlock(cursor.selectionStart()).blockNumber()
        last = document.findBlock(cursor.selectionEnd()).blockNumber()
        positions: list[int] = []
        for line in range(first, last + 1):
            block = document.findBlockByNumber(line)
            if block.isValid():
                positions.append(block.position() + len(block.text()))
        # 主游標留在最後一行，其餘交給額外游標
        # The primary caret keeps the last line; the rest become extra carets
        self._positions = sorted(set(positions[:-1]))
        main = self._code_edit.textCursor()
        main.setPosition(positions[-1] if positions else cursor.position())
        self._code_edit.setTextCursor(main)
        self._code_edit.viewport().update()
        return len(self._positions)

    def _edit_targets(self) -> list[int]:
        """
        取得所有要編輯的位置（含主游標），由小到大
        Every position to edit, primary caret included, in ascending order.
        """
        return sorted({*self._positions, self._code_edit.textCursor().position()})

    def _apply_at_targets(self, edit, shift_per_target: int) -> None:
        """
        由後往前在每個位置套用一次編輯，再把游標移到新位置
        Apply one edit at each position from the end backwards, then move the
        carets to where they ended up.

        由後往前做，先做的編輯就不會影響還沒處理的位置；做完之後，第 n 個位置前面
        共發生了 n 次編輯，加上自己那一次，所以位移量是 ``(n + 1) * 每次的位移``。
        Working backwards keeps an edit from moving a position not yet handled.
        Afterwards, the n-th position has n edits before it plus its own, so it
        moves by ``(n + 1) * shift_per_target``.

        :param edit: 對單一位置執行的編輯 / the edit to run at one position
        :param shift_per_target: 每次編輯造成的位移（插入為正，刪除為負）
            how far one edit moves what follows it: positive to insert, negative
            to delete
        """
        targets = self._edit_targets()
        main_position = self._code_edit.textCursor().position()
        cursor = self._code_edit.textCursor()
        cursor.beginEditBlock()
        try:
            for position in reversed(targets):
                edit(cursor, position)
        finally:
            cursor.endEditBlock()

        moved = {
            position: position + (index + 1) * shift_per_target
            for index, position in enumerate(targets)
        }
        main = self._code_edit.textCursor()
        main.setPosition(min(
            max(0, moved.get(main_position, main_position)), self._document_limit()))
        self._code_edit.setTextCursor(main)
        self._positions = clamp_positions(
            [moved[position] for position in self._positions if position in moved],
            self._document_limit())
        self._code_edit.viewport().update()

    def insert_text(self, text: str) -> bool:
        """
        在每個游標插入文字
        Insert text at every caret.

        :param text: 要插入的文字 / the text to insert
        :return: 有插入時為 ``True`` / ``True`` when anything was inserted
        """
        if not self._positions or not text:
            return False

        def insert(cursor: QTextCursor, position: int) -> None:
            cursor.setPosition(position)
            cursor.insertText(text)

        self._apply_at_targets(insert, len(text))
        return True

    def delete_before(self) -> bool:
        """
        在每個游標刪除前一個字元（Backspace）
        Delete the character before every caret, as Backspace does.

        任何一個游標已經在文件開頭時就整批不做，因為那一個沒有東西可刪，其餘照做
        會讓各游標的相對位置錯開。
        Nothing is deleted when any caret sits at the very start: that one has
        nothing to delete, and deleting for the others would pull the carets out
        of step with each other.

        :return: 有刪除時為 ``True`` / ``True`` when anything was deleted
        """
        if not self._positions or any(position <= 0 for position in self._edit_targets()):
            return False

        def delete(cursor: QTextCursor, position: int) -> None:
            cursor.setPosition(position)
            cursor.deletePreviousChar()

        self._apply_at_targets(delete, -1)
        return True

    def _document_limit(self) -> int:
        """文件中最大的有效位置 / The highest valid position in the document."""
        return max(0, self._code_edit.document().characterCount() - 1)

    def refresh_after_external_edit(self) -> None:
        """
        文件被其他方式改動後，把游標拉回有效範圍
        Pull the carets back into range after the document changed elsewhere.
        """
        self._positions = clamp_positions(self._positions, self._document_limit())

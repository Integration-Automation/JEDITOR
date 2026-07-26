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

from je_editor.utils.multi_cursor.cursor_positions import (
    add_position, clamp_positions, column_caret_columns, column_span, toggle_position
)


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

    def _apply_at_targets(
            self, edit, shift_per_target: int, shift_others: int | None = None) -> None:
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
        :param shift_per_target: 這個位置自己編輯後要移動多少（插入為正，Backspace
            為負，Delete 為 0，因為刪的是游標後面的字元）
            how far this position itself moves after its own edit: positive to
            insert, negative for Backspace, zero for Delete, which removes the
            character after the caret
        :param shift_others: 每次編輯讓「後面的位置」移動多少；省略時與
            *shift_per_target* 相同
            how far each edit moves the positions after it; defaults to
            *shift_per_target*
        """
        following = shift_per_target if shift_others is None else shift_others
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
            position: position + index * following + shift_per_target
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

    def delete_after(self) -> bool:
        """
        在每個游標刪除後一個字元（Delete）
        Delete the character after every caret, as Delete does.

        任何一個游標已經在文件結尾時就整批不做，理由與 Backspace 相同。
        Nothing is deleted when any caret sits at the very end, for the same
        reason as Backspace.

        :return: 有刪除時為 ``True`` / ``True`` when anything was deleted
        """
        limit = self._document_limit()
        if not self._positions or any(position >= limit for position in self._edit_targets()):
            return False

        def delete(cursor: QTextCursor, position: int) -> None:
            cursor.setPosition(position)
            cursor.deleteChar()

        # 刪除的是游標之後的字元，游標自己不動，只有其後的位置要往前
        # The character after the caret goes, so the caret stays where it is and
        # only what follows shifts back
        self._apply_at_targets(delete, 0, shift_others=-1)
        return True

    def insert_newline(self) -> bool:
        """
        在每個游標插入換行
        Insert a line break at every caret.

        :return: 有插入時為 ``True`` / ``True`` when anything was inserted
        """
        return self.insert_text("\n")

    def move_all(self, offset: int) -> bool:
        """
        把每個游標左右移動
        Move every caret left or right.

        主游標也要一起走，否則按一次方向鍵就會讓它落在別的游標後面。
        The primary caret moves too, or one press of an arrow key would leave it
        behind the others.

        :param offset: 移動量（負數往左）/ how far to move, negative for left
        :return: 有移動時為 ``True`` / ``True`` when the carets moved
        """
        if not self._positions:
            return False
        limit = self._document_limit()
        self._positions = clamp_positions(
            [position + offset for position in self._positions], limit)
        self._move_primary_to(self._code_edit.textCursor().position() + offset)
        return True

    def move_all_vertically(self, direction: int) -> bool:
        """
        把每個游標上下移動一行，保持各自的欄位
        Move every caret one line up or down, each keeping its column.

        比目標行長度更靠右的游標停在該行的行尾，與一般游標的行為一致。
        A caret further right than the target line stops at that line's end, the
        same as an ordinary caret does.

        :param direction: ``-1`` 為上一行，``1`` 為下一行 / ``-1`` up, ``1`` down
        :return: 有移動時為 ``True`` / ``True`` when the carets moved
        """
        if not self._positions:
            return False
        # 沒有那一行的游標留在原地，而不是消失
        # A caret with no line to move to stays where it is rather than vanishing
        self._positions = clamp_positions(
            [self._neighbour_or_here(position, direction) for position in self._positions],
            self._document_limit())
        self._move_primary_to(self._neighbour_or_here(
            self._code_edit.textCursor().position(), direction))
        return True

    def _neighbour_or_here(self, position: int, direction: int) -> int:
        """上下一行的同一欄，沒有那一行時維持原位 / The same column one line away, or where it is."""
        moved = self._line_neighbour(position, direction)
        return position if moved is None else moved

    def move_all_to_line_edge(self, to_end: bool) -> bool:
        """
        把每個游標移到所在行的行首或行尾
        Move every caret to the start or the end of its own line.

        :param to_end: ``True`` 移到行尾，``False`` 移到行首 / ``True`` for the end
        :return: 有移動時為 ``True`` / ``True`` when the carets moved
        """
        if not self._positions:
            return False
        self._positions = clamp_positions(
            [self._line_edge(position, to_end) for position in self._positions],
            self._document_limit())
        self._move_primary_to(
            self._line_edge(self._code_edit.textCursor().position(), to_end))
        return True

    def _line_neighbour(self, position: int, direction: int) -> int | None:
        """
        取得同一欄在上下一行的位置
        The position one line up or down, at the same column.

        :param position: 目前位置 / where the caret is
        :param direction: ``-1`` 為上一行，``1`` 為下一行 / ``-1`` up, ``1`` down
        :return: 新位置，沒有那一行時為 ``None`` / the new position, or ``None``
        """
        document = self._code_edit.document()
        block = document.findBlock(position)
        target = document.findBlockByNumber(block.blockNumber() + direction)
        if not target.isValid():
            return None
        column = position - block.position()
        return target.position() + min(column, len(target.text()))

    def _line_edge(self, position: int, to_end: bool) -> int:
        """
        取得所在行的行首或行尾位置
        The position at the start or the end of a caret's line.

        :param position: 目前位置 / where the caret is
        :param to_end: ``True`` 取行尾 / ``True`` for the end of the line
        :return: 新位置 / the new position
        """
        block = self._code_edit.document().findBlock(position)
        return block.position() + (len(block.text()) if to_end else 0)

    def _move_primary_to(self, position: int) -> None:
        """把主游標移到指定位置並重畫 / Move the primary caret there and repaint."""
        main = self._code_edit.textCursor()
        main.setPosition(min(max(0, position), self._document_limit()))
        self._code_edit.setTextCursor(main)
        self._code_edit.viewport().update()

    def select_column(self, anchor_position: int, current_position: int) -> int:
        """
        以矩形範圍在每一行放一個游標
        Put a caret on every line a rectangle covers.

        這就是欄選取：從起點拖到目前位置，涵蓋的每一行都在同一欄得到一個游標，
        比該欄短的行則停在行尾。
        This is column selection: dragging from the anchor to here gives every
        covered line a caret at the same column, with shorter lines stopping at
        their end.

        :param anchor_position: 拖曳起點的字元位置 / where the drag started
        :param current_position: 目前的字元位置 / where the pointer is now
        :return: 額外游標的數量 / how many extra carets there now are
        """
        document = self._code_edit.document()
        anchor_block = document.findBlock(anchor_position)
        current_block = document.findBlock(current_position)
        lines = column_span(anchor_block.blockNumber(), current_block.blockNumber())
        blocks = [document.findBlockByNumber(line) for line in lines]
        blocks = [block for block in blocks if block.isValid()]
        if not blocks:
            return 0
        columns = column_caret_columns(
            anchor_position - anchor_block.position(),
            current_position - current_block.position(),
            [len(block.text()) for block in blocks],
        )
        positions = [
            block.position() + column for block, column in zip(blocks, columns)
        ]
        # 主游標留在拖曳到的那一行，其餘是額外游標
        # The primary caret keeps the line the drag reached; the rest are extra
        main_position = positions[-1] if current_block.blockNumber() >= anchor_block.blockNumber() \
            else positions[0]
        self._positions = sorted(set(positions) - {main_position})
        main = self._code_edit.textCursor()
        main.setPosition(min(main_position, self._document_limit()))
        self._code_edit.setTextCursor(main)
        self._code_edit.viewport().update()
        return len(self._positions)

    def add_caret_on_neighbouring_line(self, direction: int) -> bool:
        """
        在上一行或下一行的同一欄加一個游標
        Add a caret on the line above or below, at the same column.

        :param direction: ``-1`` 為上一行，``1`` 為下一行 / ``-1`` above, ``1`` below
        :return: 有加入時為 ``True`` / ``True`` when a caret was added
        """
        document = self._code_edit.document()
        cursor = self._code_edit.textCursor()
        reference = max(self._positions, default=cursor.position()) if direction > 0 else \
            min(self._positions, default=cursor.position())
        block = document.findBlock(reference)
        column = reference - block.position()
        target = document.findBlockByNumber(block.blockNumber() + direction)
        if not target.isValid():
            return False
        position = target.position() + min(column, len(target.text()))
        self._positions = add_position(self._positions, position)
        self._code_edit.viewport().update()
        return True

    def add_caret_at_next_occurrence(self) -> bool:
        """
        在游標所在字詞的下一個出現處加一個游標
        Add a caret at the next occurrence of the word under the caret.

        游標放在該字詞的結尾，接著輸入就會接在它後面——這是「同時改掉每一處」
        最常用的形式。
        The caret goes to the end of that occurrence, so typing continues after
        it, which is the form most used for changing every occurrence at once.

        :return: 找到並加入時為 ``True`` / ``True`` when another occurrence was found
        """
        cursor = self._code_edit.textCursor()
        word_cursor = self._code_edit.textCursor()
        word_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = word_cursor.selectedText()
        if not word:
            return False
        text = self._code_edit.toPlainText()
        start_from = max([cursor.position(), *self._positions], default=0)
        found = text.find(word, start_from)
        if found < 0:
            # 找到檔尾就從頭再找一次，與其他編輯器的行為一致
            # Wrapping to the top matches what other editors do
            found = text.find(word)
            if found < 0 or found + len(word) in self._positions:
                return False
        self._positions = add_position(self._positions, found + len(word))
        self._code_edit.viewport().update()
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

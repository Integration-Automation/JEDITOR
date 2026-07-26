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
    add_position, clamp_positions, column_caret_columns, column_span,
    positions_after_replacing, toggle_position
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
        # 有選取範圍的游標：位置對應它的錨點 / A caret with a selection, mapped to its anchor
        self._anchors: dict[int, int] = {}

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
        self._anchors = {}
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

    def selections(self) -> list[tuple[int, int]]:
        """
        取得每個額外游標的選取範圍
        Each extra caret's selection.

        :return: ``(起, 訖)`` 的清單，只含真的有選取的游標
            / the ``(start, end)`` pairs, only for carets that have a selection
        """
        return sorted(
            (min(anchor, position), max(anchor, position))
            for position, anchor in self._anchors.items()
            if anchor != position and position in self._positions
        )

    def has_selections(self) -> bool:
        """是否有任何游標帶著選取範圍 / Whether any caret holds a selection."""
        return bool(self.selections()) or self._code_edit.textCursor().hasSelection()

    def _range_for(self, position: int) -> tuple[int, int]:
        """
        取得一個游標涵蓋的範圍
        The range one caret covers.

        有選取範圍就是那一段，否則是游標本身（長度為零）。
        A caret with a selection covers it, and one without covers just itself.

        :param position: 游標位置 / the caret's position
        :return: ``(起, 訖)``，訖不含 / ``(start, end)``, end exclusive
        """
        if position == self._code_edit.textCursor().position():
            cursor = self._code_edit.textCursor()
            if cursor.hasSelection():
                return cursor.selectionStart(), cursor.selectionEnd()
        anchor = self._anchors.get(position, position)
        return min(anchor, position), max(anchor, position)

    def _replace_ranges(self, ranges: list[tuple[int, int]], text: str) -> None:
        """
        把每個範圍換成同一段文字，並把游標移到各自的新位置
        Replace every range with the same text, then move each caret after its own.

        由後往前改寫，先做的改寫就不會挪動還沒處理的範圍。
        The rewrite runs back to front, so an earlier one cannot move a range that
        has not been handled yet.

        :param ranges: 要改寫的範圍 / the ranges to rewrite
        :param text: 換上去的文字 / the text to put in their place
        """
        ordered = sorted(ranges)
        main_range = self._range_for(self._code_edit.textCursor().position())
        cursor = self._code_edit.textCursor()
        cursor.beginEditBlock()
        try:
            for start, end in reversed(ordered):
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                cursor.insertText(text)
        finally:
            cursor.endEditBlock()

        moved = dict(zip(ordered, positions_after_replacing(ordered, len(text))))
        limit = self._document_limit()
        self._anchors = {}
        self._positions = clamp_positions(
            [moved[item] for item in ordered if item != main_range], limit)
        main = self._code_edit.textCursor()
        main.setPosition(min(max(0, moved.get(main_range, main_range[0])), limit))
        self._code_edit.setTextCursor(main)
        self._code_edit.viewport().update()

    def _all_ranges(self, fallback) -> list[tuple[int, int]]:
        """
        取得每個游標要編輯的範圍
        The range each caret edits.

        :param fallback: 沒有選取範圍時要用的範圍 / what to use for a caret without a selection
        :return: 每個游標的範圍 / one range per caret
        """
        ranges = []
        for position in self._edit_targets():
            start, end = self._range_for(position)
            ranges.append((start, end) if end > start else fallback(position))
        return ranges

    def insert_text(self, text: str) -> bool:
        """
        在每個游標插入文字
        Insert text at every caret.

        :param text: 要插入的文字 / the text to insert
        :return: 有插入時為 ``True`` / ``True`` when anything was inserted
        """
        if not self._positions or not text:
            return False
        # 有選取範圍的游標是「取代」，沒有的是「插入」；兩者都是把範圍換成這段文字
        # A caret with a selection replaces it and one without inserts; both are
        # the same operation on a range
        self._replace_ranges(
            self._all_ranges(lambda position: (position, position)), text)
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
        if not self._positions:
            return False
        ranges = self._all_ranges(lambda position: (position - 1, position))
        if any(start < 0 for start, _end in ranges):
            return False
        self._replace_ranges(ranges, "")
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
        if not self._positions:
            return False
        ranges = self._all_ranges(lambda position: (position, position + 1))
        if any(end > limit for _start, end in ranges):
            return False
        self._replace_ranges(ranges, "")
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
        self._anchors = {}
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
        self._anchors = {}
        # 沒有那一行的游標留在原地，而不是消失
        # A caret with no line to move to stays where it is rather than vanishing
        self._positions = clamp_positions(
            [self._neighbour_or_here(position, direction) for position in self._positions],
            self._document_limit())
        self._move_primary_to(self._neighbour_or_here(
            self._code_edit.textCursor().position(), direction))
        return True

    def extend_all(self, offset: int) -> bool:
        """
        以每個游標為基準左右擴大選取範圍
        Extend every caret's selection left or right.

        :param offset: 移動量（負數往左）/ how far to move, negative for left
        :return: 有擴大時為 ``True`` / ``True`` when the selections grew
        """
        return self._extend(lambda position: position + offset)

    def extend_all_vertically(self, direction: int) -> bool:
        """
        以每個游標為基準上下擴大選取範圍
        Extend every caret's selection one line up or down.

        :param direction: ``-1`` 為上一行，``1`` 為下一行 / ``-1`` up, ``1`` down
        :return: 有擴大時為 ``True`` / ``True`` when the selections grew
        """
        return self._extend(lambda position: self._neighbour_or_here(position, direction))

    def extend_all_to_line_edge(self, to_end: bool) -> bool:
        """
        把每個游標的選取範圍延伸到所在行的行首或行尾
        Extend every caret's selection to the start or end of its own line.

        :param to_end: ``True`` 延伸到行尾 / ``True`` for the end of the line
        :return: 有擴大時為 ``True`` / ``True`` when the selections grew
        """
        return self._extend(lambda position: self._line_edge(position, to_end))

    def _extend(self, move) -> bool:
        """
        移動每個游標但保留錨點，選取範圍因此跟著長大
        Move every caret while keeping its anchor, so the selection grows with it.

        錨點記的是選取開始的地方；已經在選取中的游標沿用原本的錨點，其餘就以目前
        位置作為錨點。
        The anchor is where the selection began: a caret already selecting keeps
        the one it has, and any other takes its current position as the anchor.

        :param move: 算出新位置的函式 / works out the new position
        :return: 有移動時為 ``True`` / ``True`` when the carets moved
        """
        if not self._positions:
            return False
        limit = self._document_limit()
        anchors: dict[int, int] = {}
        moved: list[int] = []
        for position in self._positions:
            anchor = self._anchors.get(position, position)
            landed = min(max(0, move(position)), limit)
            moved.append(landed)
            anchors[landed] = anchor
        self._positions = clamp_positions(moved, limit)
        self._anchors = {
            position: anchor for position, anchor in anchors.items()
            if position in self._positions
        }
        main = self._code_edit.textCursor()
        main.setPosition(min(max(0, move(main.position())), limit),
                         QTextCursor.MoveMode.KeepAnchor)
        self._code_edit.setTextCursor(main)
        self._code_edit.viewport().update()
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
        self._anchors = {}
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

"""
維護多重游標的位置
Keep track of where the extra carets are.

在其中一個位置插入或刪除文字之後，排在後面的位置都要跟著位移，否則第二個之後
的游標就會落在錯的地方。這裡只做位置運算，實際編輯交給編輯器。
Inserting or deleting at one caret shifts every caret after it; without that,
the second and later carets would land in the wrong place. This module does the
arithmetic only, leaving the editing to the editor.
"""
from __future__ import annotations


def add_position(positions: list[int], position: int) -> list[int]:
    """
    加入一個游標位置（已存在則不重複加入）
    Add a caret position, ignoring one that is already there.

    :param positions: 現有位置 / the positions so far
    :param position: 要加入的位置 / the position to add
    :return: 排序後的新清單 / the new sorted list
    """
    if position < 0 or position in positions:
        return sorted(positions)
    return sorted([*positions, position])


def remove_position(positions: list[int], position: int) -> list[int]:
    """
    移除一個游標位置
    Remove a caret position.

    :param positions: 現有位置 / the positions so far
    :param position: 要移除的位置 / the position to remove
    :return: 排序後的新清單 / the new sorted list
    """
    return sorted(value for value in positions if value != position)


def toggle_position(positions: list[int], position: int) -> list[int]:
    """
    切換一個游標位置：不在就加入，已在就移除
    Toggle a caret position: add it when absent, remove it when present.

    :param positions: 現有位置 / the positions so far
    :param position: 要切換的位置 / the position to toggle
    :return: 排序後的新清單 / the new sorted list
    """
    if position in positions:
        return remove_position(positions, position)
    return add_position(positions, position)


def shift_after_insert(positions: list[int], at: int, length: int) -> list[int]:
    """
    在 *at* 插入 *length* 個字元之後，調整其他位置
    Adjust the positions after *length* characters are inserted at *at*.

    插入點之後的位置往後移；插入點本身與之前的位置不變。
    Positions after the insertion move along; the insertion point itself and
    anything before it stay put.

    :param positions: 現有位置 / the positions so far
    :param at: 插入位置 / where the text went in
    :param length: 插入的字元數 / how many characters were inserted
    :return: 調整後的位置 / the adjusted positions
    """
    return [value + length if value > at else value for value in positions]


def shift_after_delete(positions: list[int], at: int, length: int) -> list[int]:
    """
    在 *at* 刪除 *length* 個字元之後，調整其他位置
    Adjust the positions after *length* characters are deleted from *at*.

    落在被刪除範圍內的位置會被移到刪除點，避免指向已經不存在的位置。
    A position inside the deleted range collapses onto the deletion point, so it
    cannot point at text that no longer exists.

    :param positions: 現有位置 / the positions so far
    :param at: 刪除起點 / where the deletion started
    :param length: 刪除的字元數 / how many characters were deleted
    :return: 調整後的位置（去重並排序）/ the adjusted positions, unique and sorted
    """
    adjusted: list[int] = []
    for value in positions:
        if value <= at:
            adjusted.append(value)
        elif value >= at + length:
            adjusted.append(value - length)
        else:
            adjusted.append(at)
    return sorted(set(adjusted))


def column_span(anchor_line: int, current_line: int) -> range:
    """
    取得欄選取涵蓋的行範圍（可上可下）
    The lines a column selection covers, dragged in either direction.

    :param anchor_line: 起點所在行 / the line the drag started on
    :param current_line: 目前所在行 / the line the pointer is on now
    :return: 涵蓋的行號，含頭含尾 / the lines covered, both ends included
    """
    first, last = sorted((max(0, anchor_line), max(0, current_line)))
    return range(first, last + 1)


def column_caret_columns(
        anchor_column: int, current_column: int, line_lengths: list[int]) -> list[int]:
    """
    取得欄選取在每一行的欄位
    The column a rectangular selection lands on for each line it covers.

    游標放在拖曳到的那一欄；比該欄短的行就停在行尾，因此短行不會產生指向不存在
    位置的游標。
    The caret goes to the column the pointer reached, and a line shorter than
    that stops at its end, so a short line never gets a caret pointing past it.

    :param anchor_column: 起點的欄位 / the column the drag started at
    :param current_column: 目前的欄位 / the column the pointer is at now
    :param line_lengths: 各涵蓋行的長度 / the length of each covered line
    :return: 各行的欄位 / the column for each line
    """
    target = max(0, current_column if current_column != anchor_column else anchor_column)
    return [min(target, max(0, length)) for length in line_lengths]


def positions_after_replacing(ranges: list[tuple[int, int]], length: int) -> list[int]:
    """
    把每個範圍都換成等長的文字之後，各游標落在哪裡
    Where each caret lands once every range is replaced by text of one length.

    範圍由前往後累積位移：排在越後面的範圍，前面被改寫的次數越多。游標停在自己
    那段新文字的結尾，接著輸入就會接在後面。
    The shift accumulates front to back, since a later range has more rewrites
    ahead of it. Each caret ends up after its own new text, so typing carries on
    from there.

    :param ranges: 每個游標涵蓋的範圍 ``(起, 訖)``，訖不含 / each caret's ``(start, end)``, end exclusive
    :param length: 換上去的文字長度 / the length of the text replacing each range
    :return: 各游標的新位置（依原順序）/ the new caret positions, in the given order
    """
    shift = 0
    moved: list[int] = []
    for start, end in sorted(ranges):
        moved.append(start + shift + length)
        shift += length - (end - start)
    return moved


def clamp_positions(positions: list[int], limit: int) -> list[int]:
    """
    把位置限制在文件範圍內
    Clamp the positions to the document's length.

    :param positions: 現有位置 / the positions so far
    :param limit: 文件可用的最大位置 / the highest valid position
    :return: 範圍內的位置（去重並排序）/ the in-range positions, unique and sorted
    """
    if limit < 0:
        return []
    return sorted({min(max(0, value), limit) for value in positions})

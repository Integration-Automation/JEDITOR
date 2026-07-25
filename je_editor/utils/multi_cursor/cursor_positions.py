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

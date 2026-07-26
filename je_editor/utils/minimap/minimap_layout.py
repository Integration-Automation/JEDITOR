"""
縮圖（minimap）的座標換算
Work out the minimap's geometry.

把「第幾行」與「縮圖上的第幾個像素」互相對應，並在行數多到畫不下時決定取樣間隔。
Maps a line number to a pixel row in the minimap and back, and decides how to
sample when there are more lines than pixels to draw them on.

純邏輯，不含 Qt，因此可以單獨測試。
Pure logic with no Qt, so it can be tested on its own.
"""
from __future__ import annotations

# 縮圖上每一行佔的像素高度 / How many pixels one line occupies in the minimap
LINE_PIXELS = 2
# 縮圖的寬度（像素）/ The minimap's width in pixels
MINIMAP_WIDTH = 90
# 一行畫成長條時，一個字元佔的寬度（像素）
# How wide one character is when a line is drawn as a bar
CHAR_PIXELS = 1


def sample_step(total_lines: int, available_height: int) -> int:
    """
    決定取樣間隔：行數多到畫不下時，每隔幾行畫一條
    How many lines each drawn row stands for when they cannot all be drawn.

    :param total_lines: 文件總行數 / the document's line count
    :param available_height: 縮圖可用高度（像素）/ the minimap's height in pixels
    :return: 取樣間隔，至少為 1 / the step, never below 1
    """
    if total_lines <= 0 or available_height <= 0:
        return 1
    drawable = max(1, available_height // LINE_PIXELS)
    if total_lines <= drawable:
        return 1
    return -(-total_lines // drawable)  # 無條件進位 / round up


def row_for_line(line: int, step: int) -> int:
    """
    取得某一行在縮圖上的像素位置
    The pixel row a line is drawn at.

    :param line: 以 0 起算的行號 / the 0-based line number
    :param step: 取樣間隔 / the sampling step
    :return: 縮圖上的 y 座標 / the y coordinate in the minimap
    """
    return (line // max(1, step)) * LINE_PIXELS


def line_at_row(row: int, step: int, total_lines: int) -> int:
    """
    取得縮圖上某個像素位置對應的行號
    The line a pixel row in the minimap points at.

    :param row: 縮圖上的 y 座標 / the y coordinate in the minimap
    :param step: 取樣間隔 / the sampling step
    :param total_lines: 文件總行數 / the document's line count
    :return: 以 0 起算的行號，會夾在文件範圍內 / the 0-based line, clamped to the document
    """
    if total_lines <= 0:
        return 0
    line = (max(0, row) // LINE_PIXELS) * max(1, step)
    return min(line, total_lines - 1)


def bar_width(text: str, width_limit: int = MINIMAP_WIDTH) -> int:
    """
    取得一行畫成長條時的寬度
    How wide a line's bar should be.

    以行的長度表示，因此縮圖看起來像程式碼的輪廓；空白行寬度為零。
    The width follows the line's length, so the minimap reads as the shape of the
    code; a blank line has no bar at all.

    :param text: 該行文字 / the line's text
    :param width_limit: 縮圖寬度上限 / the minimap's width
    :return: 長條寬度（像素）/ the bar's width in pixels
    """
    stripped = text.rstrip()
    if not stripped:
        return 0
    return min(len(stripped) * CHAR_PIXELS, width_limit)


def bar_offset(text: str, width_limit: int = MINIMAP_WIDTH) -> int:
    """
    取得一行長條的起始位置（依縮排縮進）
    Where a line's bar starts, following its indentation.

    :param text: 該行文字 / the line's text
    :param width_limit: 縮圖寬度上限 / the minimap's width
    :return: 起始 x 座標 / the starting x coordinate
    """
    indent = len(text) - len(text.lstrip())
    return min(indent * CHAR_PIXELS, width_limit)


def viewport_band(first_visible: int, visible_lines: int, step: int) -> tuple[int, int]:
    """
    取得代表目前可視範圍的方框位置與高度
    The position and height of the band showing what is currently on screen.

    :param first_visible: 畫面最上方的行號 / the top visible line
    :param visible_lines: 畫面可容納的行數 / how many lines fit on screen
    :param step: 取樣間隔 / the sampling step
    :return: ``(起始 y, 高度)``，高度至少 ``LINE_PIXELS`` / ``(top, height)``
    """
    top = row_for_line(max(0, first_visible), step)
    height = max(LINE_PIXELS, row_for_line(max(1, visible_lines), step))
    return top, height

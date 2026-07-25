"""
計算縮排參考線與尾端空白的位置
Work out where indent guides and trailing whitespace sit on a line.

繪製交給編輯器，這裡只做位置計算，因此可以單獨測試。
The editor does the drawing; this only computes positions, so it can be tested
on its own.
"""
from __future__ import annotations

# 一行最多畫幾條參考線，避免極深縮排時畫滿整行
# How many guides one line may show, so very deep indentation cannot fill it
MAX_GUIDES_PER_LINE = 16


def leading_space_width(text: str, tab_size: int) -> int:
    """
    計算一行前導空白的顯示寬度（tab 換算成空格）
    The display width of a line's leading whitespace, counting a tab as *tab_size*.

    :param text: 該行文字 / the line's text
    :param tab_size: 一個 tab 相當於幾個空格 / how many spaces a tab stands for
    :return: 前導空白的寬度 / the width of the leading whitespace
    """
    width = 0
    for character in text:
        if character == " ":
            width += 1
        elif character == "\t":
            # tab 跳到下一個定位點，不是固定加 tab_size
            # A tab advances to the next stop rather than adding a fixed amount
            width += tab_size - (width % tab_size)
        else:
            break
    return width


def guide_columns(text: str, indent_size: int) -> list[int]:
    """
    取得一行要畫縮排參考線的欄位
    The columns where a line should show indent guides.

    只在該行自己的縮排範圍內畫；空白行沒有縮排資訊，因此不畫，免得畫出誤導的線。
    Guides are drawn only within the line's own indentation. A blank line carries
    no indentation information, so it shows none rather than a misleading one.

    :param text: 該行文字 / the line's text
    :param indent_size: 一層縮排的寬度 / the width of one indentation level
    :return: 要畫線的欄位（0 起算）/ the 0-based columns to draw at
    """
    if indent_size <= 0 or not text.strip():
        return []
    width = leading_space_width(text, indent_size)
    levels = min(width // indent_size, MAX_GUIDES_PER_LINE)
    return [level * indent_size for level in range(1, levels + 1)]


def trailing_whitespace_start(text: str) -> int | None:
    """
    取得一行尾端空白的起始位置
    Where a line's trailing whitespace starts.

    整行都是空白時視為尾端空白；完全空白的行不算（那只是空行）。
    A line of nothing but whitespace counts, while an empty line does not, since
    that is simply a blank line.

    :param text: 該行文字 / the line's text
    :return: 起始字元索引，沒有尾端空白時為 ``None`` / the index, or ``None``
    """
    if not text:
        return None
    stripped = text.rstrip()
    if len(stripped) == len(text):
        return None
    return len(stripped)

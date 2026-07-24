"""
縮排轉換（純邏輯，不含 Qt）
Indentation conversion (pure logic, no Qt imports).

只轉換每行「開頭」的空白，行內（例如字串或對齊用）的 Tab 或空白保持不變，
因此不會破壞字串內容或行內對齊。
Only the *leading* whitespace of each line is converted; tabs or spaces later in
the line (inside strings, or used for alignment) are left untouched, so string
contents and inline alignment are never corrupted.
"""
from __future__ import annotations

_NEWLINE = "\n"
# 預設每個 Tab 對應的空白數 / Default number of spaces per tab
DEFAULT_TAB_SIZE = 4


def _split_leading_whitespace(line: str) -> tuple[str, str]:
    """把一行拆成（開頭空白, 其餘內容）/ Split a line into (leading whitespace, rest)."""
    stripped = line.lstrip(" \t")
    leading = line[: len(line) - len(stripped)]
    return leading, stripped


def _leading_width(leading: str, tab_size: int) -> int:
    """計算開頭空白展開後的欄位數 / The column width of leading whitespace once expanded."""
    width = 0
    for char in leading:
        if char == "\t":
            # Tab 前進到下一個 tab stop / A tab advances to the next tab stop
            width += tab_size - (width % tab_size)
        else:
            width += 1
    return width


def convert_leading_tabs_to_spaces(text: str, tab_size: int = DEFAULT_TAB_SIZE) -> str:
    """
    把每行開頭的 Tab 轉成空白
    Convert the leading tabs of each line into spaces.

    :param text: 原始文字 / The original text
    :param tab_size: 每個 Tab 對應的空白數 / Spaces per tab
    :return: 轉換後的文字 / The converted text
    """
    tab_size = max(1, tab_size)
    converted_lines = []
    for line in text.split(_NEWLINE):
        leading, rest = _split_leading_whitespace(line)
        if "\t" in leading:
            leading = " " * _leading_width(leading, tab_size)
        converted_lines.append(leading + rest)
    return _NEWLINE.join(converted_lines)


def convert_leading_spaces_to_tabs(text: str, tab_size: int = DEFAULT_TAB_SIZE) -> str:
    """
    把每行開頭的空白轉成 Tab
    Convert the leading spaces of each line into tabs.

    每 ``tab_size`` 個欄位換成一個 Tab，剩下不足一個 Tab 的欄位保留為空白。
    Every ``tab_size`` columns becomes one tab; a remainder smaller than a full tab
    stays as spaces.

    :param text: 原始文字 / The original text
    :param tab_size: 每個 Tab 對應的空白數 / Spaces per tab
    :return: 轉換後的文字 / The converted text
    """
    tab_size = max(1, tab_size)
    converted_lines = []
    for line in text.split(_NEWLINE):
        leading, rest = _split_leading_whitespace(line)
        if leading:
            width = _leading_width(leading, tab_size)
            leading = "\t" * (width // tab_size) + " " * (width % tab_size)
        converted_lines.append(leading + rest)
    return _NEWLINE.join(converted_lines)


def detect_indent_width(text: str) -> int | None:
    """
    偵測以空白縮排的檔案每一層用幾個空白
    Detect how many spaces make one indent level in a space-indented file.

    先看相鄰行縮排「增加」時的差距，取最常見的差距；沒有任何增加時退而取最小的
    非零縮排。完全沒有空白縮排時回傳 ``None``。
    Looks at the increase in leading spaces between consecutive lines and takes the
    most common step; with no increases it falls back to the smallest non-zero
    indent. Returns ``None`` when there is no space indentation at all.

    :param text: 檔案內容 / The file text
    :return: 每層縮排的空白數，無法判斷時回傳 ``None``
        / Spaces per indent level, or ``None`` when undecidable
    """
    indents: list[int] = []
    for line in text.split(_NEWLINE):
        if line.strip() == "" or line[:1] not in (" ",):
            continue
        indents.append(len(line) - len(line.lstrip(" ")))
    if not indents:
        return None

    step_counts: dict[int, int] = {}
    previous = 0
    for indent in indents:
        step = indent - previous
        if step > 0:
            step_counts[step] = step_counts.get(step, 0) + 1
        previous = indent

    if step_counts:
        # 取出現次數最多的縮排差；同次數時取較小者較保守
        # Pick the most frequent step; ties resolve to the smaller (more conservative) step
        return min(step_counts, key=lambda step: (-step_counts[step], step))
    return min(indent for indent in indents if indent > 0) if any(indents) else None


def detect_indentation_uses_tabs(text: str) -> bool | None:
    """
    偵測檔案的縮排以 Tab 還是空白為主
    Detect whether a file indents mainly with tabs or spaces.

    只看有縮排的行的第一個字元；無法判斷時（沒有任何縮排）回傳 ``None``。
    Looks at the first character of each indented line; returns ``None`` when there
    is nothing to judge (no indented lines).

    :param text: 檔案內容 / The file text
    :return: 以 Tab 為主為 ``True``、以空白為主為 ``False``、無法判斷為 ``None``
        / ``True`` for tabs, ``False`` for spaces, ``None`` when undecidable
    """
    tab_lines = 0
    space_lines = 0
    for line in text.split(_NEWLINE):
        if not line or line[0] not in " \t" or line.strip() == "":
            continue
        if line[0] == "\t":
            tab_lines += 1
        else:
            space_lines += 1
    if tab_lines == 0 and space_lines == 0:
        return None
    return tab_lines > space_lines

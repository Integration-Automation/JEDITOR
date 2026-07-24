"""
游標處整數的尋找與加減（純邏輯，不含 Qt）
Find and adjust the integer under the caret (pure logic, no Qt imports).
"""
from __future__ import annotations


def _is_digit(text: str, index: int) -> bool:
    """判斷指定索引是否為數字 / Whether the character at ``index`` is a digit."""
    return 0 <= index < len(text) and text[index].isdigit()


def find_number_at(text: str, position: int) -> tuple[int, int, int] | None:
    """
    找出游標所在（或緊鄰）的整數
    Find the integer at, or immediately next to, the caret.

    游標可以落在數字內或數字的右緣。若數字前有一個當作正負號（而非減法運算子）的
    ``-``，也會一併納入。
    The caret may sit inside the number or just past its right edge. A leading ``-``
    that acts as a sign (rather than a subtraction operator) is included too.

    :param text: 完整文字 / The full text
    :param position: 游標字元位置 / The caret character offset
    :return: ``(start, end, value)``，游標不在數字上時回傳 ``None``
        / ``(start, end, value)``, or ``None`` when the caret is not on a number
    """
    if not text:
        return None
    pos = max(0, min(position, len(text)))
    if not _is_digit(text, pos):
        if _is_digit(text, pos - 1):
            pos -= 1
        else:
            return None

    start = pos
    while start > 0 and text[start - 1].isdigit():
        start -= 1
    end = pos
    while end < len(text) and text[end].isdigit():
        end += 1

    # 只有在 '-' 是正負號（前面不是英數字元）時才納入 / Include '-' only when it is a sign
    if start > 0 and text[start - 1] == "-" and (start - 1 == 0 or not text[start - 2].isalnum()):
        start -= 1

    return start, end, int(text[start:end])


def parse_int(text: str) -> int | None:
    """
    把文字解析成整數，支援 0x / 0o / 0b 前綴與純十進位
    Parse text into an integer, accepting 0x / 0o / 0b prefixes and plain decimal.

    :param text: 要解析的文字 / The text to parse
    :return: 整數值，無法解析時回傳 ``None`` / The integer, or ``None`` when unparseable
    """
    stripped = text.strip()
    if not stripped:
        return None
    for base in (0, 10):
        try:
            return int(stripped, base)
        except ValueError:
            continue
    return None


def to_base(text: str, base: int) -> str | None:
    """
    把文字中的整數轉成指定進位的字串表示
    Convert the integer in ``text`` into a string in the given base.

    :param text: 含整數的文字 / Text containing an integer
    :param base: 目標進位（2、8、10 或 16）/ The target base (2, 8, 10 or 16)
    :return: 轉換後字串，解析失敗或進位不支援時回傳 ``None``
        / The converted string, or ``None`` on parse failure / unsupported base
    """
    value = parse_int(text)
    if value is None:
        return None
    formatters = {2: bin, 8: oct, 10: str, 16: hex}
    formatter = formatters.get(base)
    return formatter(value) if formatter is not None else None


def adjust_number_at(text: str, position: int, delta: int) -> tuple[str, int, int] | None:
    """
    把游標處的整數加上 ``delta``
    Add ``delta`` to the integer under the caret.

    :param text: 完整文字 / The full text
    :param position: 游標字元位置 / The caret character offset
    :param delta: 增減量（可為負）/ The amount to add (may be negative)
    :return: ``(new_number_text, start, end)``，游標不在數字上時回傳 ``None``
        / ``(new_number_text, start, end)``, or ``None`` when not on a number
    """
    found = find_number_at(text, position)
    if found is None:
        return None
    start, end, value = found
    return str(value + delta), start, end

"""
依分隔符對齊多行（純邏輯，不含 Qt）
Align lines on a delimiter (pure logic, no Qt imports).

把每行第一個分隔符對齊到同一欄，常用於對齊一組 ``=`` 指派或 ``:`` 對應。
Aligns each line's first delimiter to the same column, handy for a group of ``=``
assignments or ``:`` mappings.
"""
from __future__ import annotations


def align_by_delimiter(lines: list[str], delimiter: str) -> list[str]:
    """
    把每行的第一個分隔符對齊
    Align the first occurrence of ``delimiter`` across the lines.

    不含分隔符的行保持原樣。分隔符前後各保留一個空白，分隔符前的內容以空白補齊到
    最長的一行，讓所有分隔符落在同一欄。
    Lines without the delimiter are left unchanged. One space is kept on each side of
    the delimiter, and the content before it is padded to the longest line so every
    delimiter lands in the same column.

    :param lines: 要對齊的行 / The lines to align
    :param delimiter: 對齊用的分隔符 / The delimiter to align on
    :return: 對齊後的新清單 / A new list with delimiters aligned
    """
    if not delimiter:
        return list(lines)

    positions = [line.find(delimiter) for line in lines]
    widths = [
        len(line[:index].rstrip())
        for line, index in zip(lines, positions)
        if index >= 0
    ]
    if not widths:
        return list(lines)
    target = max(widths)

    aligned: list[str] = []
    for line, index in zip(lines, positions):
        if index < 0:
            aligned.append(line)
            continue
        before = line[:index].rstrip()
        after = line[index + len(delimiter):].lstrip()
        aligned.append(f"{before.ljust(target)} {delimiter} {after}".rstrip())
    return aligned

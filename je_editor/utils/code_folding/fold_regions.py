"""
以縮排計算可折疊區塊（純邏輯，不含 Qt）
Compute foldable regions from indentation (pure logic, no Qt imports).

折疊只依據縮排，因此對 Python 以及任何用縮排表達巢狀的檔案都適用，
且完全不需要執行或匯入使用者的程式碼。
Folding is purely indentation-based, so it works for Python and any file that
expresses nesting through indentation, without importing or running user code.
"""
from __future__ import annotations

from dataclasses import dataclass

# 展開 Tab 時使用的寬度；只影響相對縮排比較，不影響顯示
# Tab expansion width; only affects relative indent comparison, not display
TAB_WIDTH = 8
# 掃描行數上限，避免病態的深層巢狀檔案造成過久的計算
# Line cap so a pathologically deep file cannot make the scan run too long
MAX_SCAN_LINES = 50000


@dataclass(frozen=True)
class FoldRegion:
    """
    一個可折疊區塊
    One foldable region.

    :param start: 標頭行（0 起算），折疊時保持可見 / The header line (0-based), stays visible
    :param end: 區塊最後一行（0 起算，含）/ The last line of the region (0-based, inclusive)
    :param indent: 標頭行的縮排欄位數 / The header line's indent column count
    """

    start: int
    end: int
    indent: int

    @property
    def body_lines(self) -> range:
        """折疊時會被隱藏的行 / The lines hidden when this region is folded."""
        return range(self.start + 1, self.end + 1)


def line_indent(line: str) -> int | None:
    """
    計算一行的縮排欄位數
    Return a line's indent as a column count.

    :param line: 原始文字行 / The raw text line
    :return: 縮排欄位數；整行空白時回傳 ``None``
        / The indent column count, or ``None`` when the line is blank
    """
    if not line.strip():
        return None
    expanded = line.expandtabs(TAB_WIDTH)
    return len(expanded) - len(expanded.lstrip())


def compute_fold_regions(lines: list[str]) -> list[FoldRegion]:
    """
    從文字行計算所有可折疊區塊
    Compute every foldable region from a list of text lines.

    一行是折疊標頭，當其後（略過空白行）存在縮排更深的行。區塊延伸到縮排掉回
    標頭層級之前的最後一個非空白行，尾端的空白行不計入。
    A line is a fold header when a more-indented line follows it (skipping blanks).
    The region runs to the last non-blank line before the indent falls back to the
    header's level; trailing blank lines are excluded.

    :param lines: 檔案的文字行 / The file's text lines
    :return: 依標頭行排序的區塊清單 / Regions ordered by header line
    """
    count = min(len(lines), MAX_SCAN_LINES)
    indents = [line_indent(lines[index]) for index in range(count)]
    regions: list[FoldRegion] = []
    for header in range(count):
        header_indent = indents[header]
        if header_indent is None:
            continue
        end = _region_end(indents, header, header_indent, count)
        if end > header:
            regions.append(FoldRegion(start=header, end=end, indent=header_indent))
    return regions


def _region_end(
        indents: list[int | None], header: int, header_indent: int, count: int) -> int:
    """
    找出區塊的最後一行
    Find the last line belonging to the region starting at ``header``.

    :return: 區塊最後一個非空白行的索引；沒有內容時回傳 ``header``
        / Index of the region's last non-blank line, or ``header`` when empty
    """
    end = header
    cursor = header + 1
    while cursor < count:
        indent = indents[cursor]
        if indent is None:
            # 空白行暫時略過，是否計入由後續是否還有內容決定
            # A blank line is tentatively skipped; inclusion depends on what follows
            cursor += 1
            continue
        if indent > header_indent:
            end = cursor
            cursor += 1
            continue
        break
    return end


def region_at_line(regions: list[FoldRegion], line: int) -> FoldRegion | None:
    """
    取得以指定行為標頭的區塊
    Return the region whose header is ``line``, if any.

    :param regions: :func:`compute_fold_regions` 的結果 / Regions from :func:`compute_fold_regions`
    :param line: 標頭行（0 起算）/ The header line (0-based)
    :return: 對應的區塊，或 ``None`` / The matching region, or ``None``
    """
    for region in regions:
        if region.start == line:
            return region
    return None

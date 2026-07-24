"""
智慧選取範圍計算（純邏輯，不含 Qt）
Smart selection range computation (pure logic, no Qt imports).

依序把選取範圍擴大到：字詞 → 整行 → 包住游標的縮排區塊（一層層往外）→ 整份文件。
Expands a selection through: word -> whole line -> enclosing indented blocks
(outward, level by level) -> the whole document.
"""
from __future__ import annotations

from je_editor.utils.code_folding.fold_regions import compute_fold_regions
from je_editor.utils.occurrence.word_occurrences import word_at

# 一個字元範圍，以起訖字元位置表示（end 不含）
# A character range expressed as start/end character offsets (end exclusive)
Range = tuple[int, int]


def _line_offsets(text: str) -> list[int]:
    """回傳每一行起始的字元位置 / The start character offset of each line."""
    offsets = [0]
    for index, char in enumerate(text):
        if char == "\n":
            offsets.append(index + 1)
    return offsets


def _line_range(text: str, line_offsets: list[int], line: int) -> Range:
    """取得某一行的字元範圍（不含換行）/ The character range of a line (excluding newline)."""
    start = line_offsets[line]
    end = line_offsets[line + 1] - 1 if line + 1 < len(line_offsets) else len(text)
    return start, end


def _line_of_offset(line_offsets: list[int], offset: int) -> int:
    """把字元位置對應到行號 / Map a character offset to a line number."""
    line = 0
    for index, start in enumerate(line_offsets):
        if start <= offset:
            line = index
        else:
            break
    return line


def candidate_ranges(text: str, position: int) -> list[Range]:
    """
    計算由小到大的候選選取範圍
    Compute candidate selection ranges from smallest to largest.

    :param text: 完整文字 / The full text
    :param position: 游標字元位置 / The caret character offset
    :return: 依範圍大小遞增排序的候選範圍 / Candidate ranges, smallest first
    """
    if not text:
        return [(0, 0)]
    position = max(0, min(position, len(text)))
    line_offsets = _line_offsets(text)
    candidates: list[Range] = []

    word = word_at(text, position)
    if word is not None:
        candidates.append((word[1], word[2]))

    current_line = _line_of_offset(line_offsets, position)
    candidates.append(_line_range(text, line_offsets, current_line))

    # 包住目前行的每個縮排區塊，由內而外 / Each indented block enclosing the line, inner first
    regions = compute_fold_regions(text.split("\n"))
    enclosing = [
        region for region in regions
        if region.start <= current_line <= region.end
    ]
    enclosing.sort(key=lambda region: region.end - region.start)
    for region in enclosing:
        start = line_offsets[region.start]
        end = _line_range(text, line_offsets, region.end)[1]
        candidates.append((start, end))

    candidates.append((0, len(text)))
    return candidates


def expand_selection(text: str, start: int, end: int) -> Range | None:
    """
    計算比目前選取更大的下一個範圍
    Compute the next range strictly larger than the current selection.

    :param text: 完整文字 / The full text
    :param start: 目前選取起點 / The current selection start offset
    :param end: 目前選取終點 / The current selection end offset
    :return: 下一個包住且更大的範圍，已是整份文件時回傳 ``None``
        / The next enclosing, larger range, or ``None`` when already the whole text
    """
    for candidate_start, candidate_end in candidate_ranges(text, start):
        contains = candidate_start <= start and candidate_end >= end
        larger = candidate_start < start or candidate_end > end
        if contains and larger:
            return candidate_start, candidate_end
    return None

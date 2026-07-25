"""
逐行比較緩衝區與基準文字，算出每一行的變更狀態
Work out, line by line, how a buffer differs from its committed baseline.

編輯器用這份結果在行號區畫出變更標記，讓「這次改了哪些行」一眼可見。
The editor paints the result in its gutter, so what changed since the last
commit is visible without leaving the file.

這個模組是純邏輯：不碰 Qt、不碰 git、不做 I/O，因此可以單獨測試。
Pure logic: no Qt, no git, no I/O, so it can be tested on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

# 一行相對於基準的狀態 / How one line differs from the baseline
LINE_ADDED = "added"
LINE_MODIFIED = "modified"
# 這一行的「上方」刪掉了內容 / Lines were deleted just above this one
LINE_REMOVED_ABOVE = "removed"

# 超過這個行數就不比較：標記只是輔助，不值得讓編輯卡住
# Buffers longer than this are not diffed: the markers are a convenience and are
# not worth stalling the edit they are meant to annotate.
MAX_DIFFED_LINES = 20000


def _split_lines(text: str) -> list[str]:
    """
    切成行；空字串視為零行，這樣新檔案的每一行都算新增
    Split into lines, treating an empty text as no lines so that every line of a
    brand-new file counts as added.
    """
    return text.splitlines() if text else []


def _mark_removal(statuses: dict[int, str], line: int, line_count: int) -> None:
    """
    在刪除位置的下一行標記；已有狀態的行不覆蓋
    Mark the line that follows a deletion, without overwriting a line that
    already carries a status of its own.
    """
    if line_count <= 0:
        return
    index = min(line, line_count - 1)
    statuses.setdefault(index, LINE_REMOVED_ABOVE)


def line_statuses(baseline: str, current: str) -> dict[int, str]:
    """
    比對基準與目前內容，回傳每行的狀態
    Compare the baseline with the current text and report each line's status.

    :param baseline: 已提交的內容 / the committed content
    :param current: 編輯中的內容 / the buffer being edited
    :return: 以 0 起算的行號對應狀態，未變更的行不在其中
        0-based line number -> status, with unchanged lines left out
    """
    current_lines = _split_lines(current)
    if len(current_lines) > MAX_DIFFED_LINES:
        return {}
    baseline_lines = _split_lines(baseline)
    if len(baseline_lines) > MAX_DIFFED_LINES:
        return {}

    statuses: dict[int, str] = {}
    matcher = SequenceMatcher(None, baseline_lines, current_lines, autojunk=False)
    for tag, _base_start, _base_end, start, end in matcher.get_opcodes():
        if tag == "replace":
            statuses.update({line: LINE_MODIFIED for line in range(start, end)})
        elif tag == "insert":
            statuses.update({line: LINE_ADDED for line in range(start, end)})
        elif tag == "delete":
            _mark_removal(statuses, start, len(current_lines))
    return statuses


@dataclass(frozen=True)
class Hunk:
    """
    一段連續的變更，以及它在基準中的對應範圍
    One run of change, and the baseline range it corresponds to.

    :param start: 目前內容中的起始行（0 起算）/ start line in the current text
    :param end: 目前內容中的結束行（不含）/ end line in the current text, exclusive
    :param baseline_start: 基準中的起始行 / start line in the baseline
    :param baseline_end: 基準中的結束行（不含）/ end line in the baseline, exclusive
    """

    start: int
    end: int
    baseline_start: int
    baseline_end: int

    @property
    def is_pure_deletion(self) -> bool:
        """這段變更是否只有刪除（目前內容中沒有對應的行）/ Whether only lines were removed."""
        return self.start == self.end

    def contains(self, line: int) -> bool:
        """
        判斷某行是否屬於這段變更
        Whether *line* belongs to this hunk.

        純刪除在目前內容中沒有範圍，因此以刪除位置那一行為準。
        A pure deletion spans no lines, so the line at the deletion point counts.

        :param line: 以 0 起算的行號 / the 0-based line number
        :return: 屬於這段變更時為 ``True`` / ``True`` when the line is inside
        """
        if self.is_pure_deletion:
            return line == self.start
        return self.start <= line < self.end


def hunks(baseline: str, current: str) -> list[Hunk]:
    """
    找出所有變更區塊
    Find every run of change between the baseline and the current text.

    :param baseline: 已提交的內容 / the committed content
    :param current: 編輯中的內容 / the buffer being edited
    :return: 變更區塊，依出現順序 / the hunks, in order
    """
    baseline_lines = _split_lines(baseline)
    current_lines = _split_lines(current)
    if max(len(baseline_lines), len(current_lines)) > MAX_DIFFED_LINES:
        return []
    matcher = SequenceMatcher(None, baseline_lines, current_lines, autojunk=False)
    return [
        Hunk(start=start, end=end, baseline_start=base_start, baseline_end=base_end)
        for tag, base_start, base_end, start, end in matcher.get_opcodes()
        if tag != "equal"
    ]


def hunk_at_line(baseline: str, current: str, line: int) -> Hunk | None:
    """
    取得包含指定行的變更區塊
    Return the hunk that contains *line*.

    :param baseline: 已提交的內容 / the committed content
    :param current: 編輯中的內容 / the buffer being edited
    :param line: 以 0 起算的行號 / the 0-based line number
    :return: 該變更區塊，該行沒有變更時為 ``None`` / the hunk, or ``None``
    """
    for hunk in hunks(baseline, current):
        if hunk.contains(line):
            return hunk
    return None


def baseline_lines_of(baseline: str, hunk: Hunk) -> list[str]:
    """
    取得一段變更在基準中的原始內容
    Return the baseline lines a hunk replaced.

    :param baseline: 已提交的內容 / the committed content
    :param hunk: 目標變更區塊 / the hunk to look up
    :return: 原始行（不含換行字元）/ the original lines, without line breaks
    """
    return _split_lines(baseline)[hunk.baseline_start:hunk.baseline_end]


def changed_line_numbers(statuses: dict[int, str]) -> list[int]:
    """
    取得有變更的行號（由小到大）
    Return the changed line numbers, in order.

    :param statuses: :func:`line_statuses` 的結果 / the statuses to read
    :return: 排序後的行號 / the line numbers, ascending
    """
    return sorted(statuses)


def next_changed_line(statuses: dict[int, str], line: int) -> int | None:
    """
    找出 *line* 之後的下一個變更行，找不到就從頭繞回
    Return the next changed line after *line*, wrapping around to the first.

    :param statuses: :func:`line_statuses` 的結果 / the statuses to read
    :param line: 目前所在行（0 起算）/ the current 0-based line
    :return: 目標行號，沒有任何變更時為 ``None``
        the line to jump to, or ``None`` when nothing changed
    """
    changed = changed_line_numbers(statuses)
    if not changed:
        return None
    for candidate in changed:
        if candidate > line:
            return candidate
    return changed[0]


def previous_changed_line(statuses: dict[int, str], line: int) -> int | None:
    """
    找出 *line* 之前的上一個變更行，找不到就繞回最後一個
    Return the previous changed line before *line*, wrapping around to the last.

    :param statuses: :func:`line_statuses` 的結果 / the statuses to read
    :param line: 目前所在行（0 起算）/ the current 0-based line
    :return: 目標行號，沒有任何變更時為 ``None``
        the line to jump to, or ``None`` when nothing changed
    """
    changed = changed_line_numbers(statuses)
    if not changed:
        return None
    for candidate in reversed(changed):
        if candidate < line:
            return candidate
    return changed[-1]

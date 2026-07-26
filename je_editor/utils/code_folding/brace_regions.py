"""
以大括號計算可折疊區塊（純邏輯，不含 Qt）
Compute foldable regions from brace pairs (pure logic, no Qt imports).

縮排式折疊對 Python 剛好，但 C 家族的語言把區塊寫在 ``{`` 與 ``}`` 之間，縮排只是
慣例——只用縮排判斷的話，把開頭的大括號放在下一行、或整段擠在一行，折疊就對不上。
Indentation folding suits Python, but the C-family languages delimit blocks with
``{`` and ``}`` and treat indentation as a convention; judging by indentation
alone then misreads a brace placed on its own line, or a block written on one.

字串與註解裡的括號不算，否則 ``"{"`` 之類的內容會讓整份檔案的配對錯開。
Braces inside strings and comments do not count, or something like ``"{"`` would
throw every pair in the file out of step.
"""
from __future__ import annotations

from dataclasses import dataclass

from je_editor.utils.code_folding.fold_regions import MAX_SCAN_LINES, FoldRegion, line_indent
from je_editor.utils.syntax.language_rules import rules_for

# 用大括號表達區塊的副檔名 / The suffixes whose blocks are delimited by braces
BRACE_SUFFIXES = frozenset({
    ".js", ".ts", ".rs", ".go", ".c", ".h", ".cpp", ".hpp", ".java", ".json",
})


@dataclass
class _ScanState:
    """
    掃描過程中的狀態
    What the scan is in the middle of.

    :param string_quote: 目前所在字串的引號，不在字串中則為空字串
        / the quote of the string being scanned, or empty when outside one
    :param in_block_comment: 是否在區塊註解中 / whether a block comment is open
    """

    string_quote: str = ""
    in_block_comment: bool = False


def uses_braces(suffix: str) -> bool:
    """
    判斷某個副檔名是否以大括號表達區塊
    Whether a file suffix delimits its blocks with braces.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 是的話為 ``True`` / ``True`` when it does
    """
    return suffix.lower() in BRACE_SUFFIXES


def compute_brace_fold_regions(lines: list[str], suffix: str) -> list[FoldRegion]:
    """
    從大括號配對計算可折疊區塊
    Compute the foldable regions from brace pairs.

    每一對括號構成一個區塊：標頭是 ``{`` 所在的行，結尾是配對的 ``}`` 所在的行。
    兩者同一行的區塊不算，折疊它沒有任何意義。
    Each pair makes a region: the header is the line holding ``{`` and the end is
    the line holding its match. A pair that opens and closes on one line is not a
    region, since folding it would hide nothing.

    :param lines: 檔案的文字行 / the file's text lines
    :param suffix: 副檔名，用來判斷字串與註解的寫法 / the suffix, for its comment syntax
    :return: 依標頭行排序的區塊 / the regions, ordered by header line
    """
    count = min(len(lines), MAX_SCAN_LINES)
    rules = rules_for(suffix)
    line_comment = rules.line_comment if rules is not None else "//"
    block_comment = rules.block_comment if rules is not None else ("/*", "*/")
    quotes = rules.string_delimiters if rules is not None else ('"', "'")
    state = _ScanState()
    open_lines: list[int] = []
    regions: list[FoldRegion] = []
    for number in range(count):
        for symbol in _braces_in(lines[number], state, line_comment, block_comment, quotes):
            if symbol == "{":
                open_lines.append(number)
            elif open_lines:
                start = open_lines.pop()
                # 至少要藏得住一行才算得上區塊；結尾的 ``}`` 留著可見
                # A region has to hide at least one line; the closing ``}`` stays visible
                if number > start + 1:
                    regions.append(FoldRegion(
                        start=start, end=number - 1, indent=line_indent(lines[start]) or 0))
    return sorted(regions, key=lambda region: region.start)


def _braces_in(line: str, state: _ScanState, line_comment: str,
               block_comment: tuple[str, str] | None, quotes: tuple[str, ...]) -> list[str]:
    """
    取出一行中真正算數的大括號
    The braces on one line that actually count.

    :param line: 一行文字 / the line of text
    :param state: 跨行延續的狀態，會被就地更新 / the state carried across lines, updated in place
    :param line_comment: 單行註解的開頭 / what starts a line comment
    :param block_comment: 區塊註解的起訖 / the block comment delimiters
    :param quotes: 字串的引號 / the quote characters
    :return: 依序出現的 ``{`` 與 ``}`` / the braces in the order they appear
    """
    found: list[str] = []
    index = 0
    while index < len(line):
        char = line[index]
        if state.in_block_comment:
            index = _skip_to_block_end(line, index, block_comment, state)
            continue
        if state.string_quote:
            index = _skip_in_string(line, index, state)
            continue
        if block_comment and line.startswith(block_comment[0], index):
            state.in_block_comment = True
            index += len(block_comment[0])
            continue
        if line_comment and line.startswith(line_comment, index):
            break
        if char in quotes:
            state.string_quote = char
            index += 1
            continue
        if char in "{}":
            found.append(char)
        index += 1
    return found


def _skip_to_block_end(line: str, index: int, block_comment: tuple[str, str] | None,
                       state: _ScanState) -> int:
    """跳過區塊註解的內容 / Step past what is inside a block comment."""
    if block_comment and line.startswith(block_comment[1], index):
        state.in_block_comment = False
        return index + len(block_comment[1])
    return index + 1


def _skip_in_string(line: str, index: int, state: _ScanState) -> int:
    """跳過字串的內容，並處理跳脫字元 / Step past a string's content, honouring escapes."""
    char = line[index]
    if char == "\\":
        return index + 2
    if char == state.string_quote:
        state.string_quote = ""
    return index + 1


def fold_regions_for(lines: list[str], suffix: str) -> list[FoldRegion]:
    """
    依語言選擇折疊方式
    Compute the foldable regions the way this language expresses blocks.

    :param lines: 檔案的文字行 / the file's text lines
    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 可折疊區塊 / the foldable regions
    """
    from je_editor.utils.code_folding.fold_regions import compute_fold_regions
    if uses_braces(suffix):
        return compute_brace_fold_regions(lines, suffix)
    return compute_fold_regions(lines)

"""
指令面板的模糊比對邏輯（純邏輯，不含 Qt）
Fuzzy matching logic for the command palette (pure logic, no Qt imports).

保持與 Qt 無關讓排序規則可以在無頭環境下單元測試。
Keeping this Qt-free lets the ranking rules be unit tested headlessly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

# 連續命中的加分 / Bonus when a query char immediately follows the previous match
SEQUENTIAL_BONUS = 15
# 命中單字開頭的加分 / Bonus when a match lands on a word boundary
WORD_BOUNDARY_BONUS = 10
# 大小寫完全相同的加分 / Bonus when the case matches exactly
CASE_BONUS = 2
# 候選字串開頭未命中的每字元扣分 / Penalty per leading unmatched char
LEADING_PENALTY = -3
# 開頭扣分的下限 / Floor for the leading penalty
MAX_LEADING_PENALTY = -9
# 候選字串多餘長度的每字元扣分 / Penalty per surplus candidate char
LENGTH_PENALTY = -1
# 長度扣分的下限 / Floor for the length penalty
MAX_LENGTH_PENALTY = -20
# 直接包含整段查詢的加分 / Bonus when the whole query appears as a substring
SUBSTRING_BONUS = 25
# 候選字串以查詢開頭的加分 / Bonus when the candidate starts with the query
PREFIX_BONUS = 20
# 比對命令標題時的權重（標題比完整路徑更重要）
# Weight applied to the title score (a title match beats a path match)
TITLE_WEIGHT = 2
# 預設回傳筆數上限 / Default cap on returned results
DEFAULT_RESULT_LIMIT = 50

# 視為單字分隔的字元 / Characters treated as word separators
WORD_SEPARATORS = frozenset(" \t_-.:/\\>()[]{}")


@dataclass
class CommandEntry:
    """
    指令面板中的一筆可執行指令
    One runnable entry shown in the command palette.

    :param title: 指令顯示名稱 / Human readable command name
    :param path: 指令在選單中的完整路徑，例如 "File > Open File"
        / Full menu path, e.g. "File > Open File"
    :param shortcut: 對應的快捷鍵文字，可為空 / Shortcut text, may be empty
    :param payload: 觸發指令所需的物件（UI 層使用），純邏輯不會碰
        / Object used by the UI layer to trigger the command; untouched here
    """

    title: str
    path: str = ""
    shortcut: str = ""
    payload: Any = field(default=None, compare=False, repr=False)

    @property
    def search_text(self) -> str:
        """回傳用於比對的完整文字 / Return the full text used for matching."""
        return self.path or self.title


def fuzzy_score(query: str, candidate: str) -> int | None:
    """
    計算查詢字串對候選字串的模糊比對分數
    Score ``query`` against ``candidate`` using a greedy subsequence match.

    :param query: 使用者輸入的查詢字串 / The user supplied query
    :param candidate: 被比對的候選字串 / The candidate string
    :return: 分數（越高越相符），完全不相符時回傳 ``None``
        / A score where higher is better, or ``None`` when there is no match
    """
    if not query:
        return 0
    if not candidate:
        return None

    lowered_query = query.lower()
    lowered_candidate = candidate.lower()

    score = 0
    search_from = 0
    previous_index = -1
    first_index = -1

    for query_index, query_char in enumerate(lowered_query):
        found = lowered_candidate.find(query_char, search_from)
        if found < 0:
            return None
        if first_index < 0:
            first_index = found
        score += _match_bonus(query, candidate, query_index, found, previous_index)
        previous_index = found
        search_from = found + 1

    score += max(MAX_LEADING_PENALTY, LEADING_PENALTY * first_index)
    score += max(MAX_LENGTH_PENALTY, LENGTH_PENALTY * (len(candidate) - len(query)))
    if lowered_query in lowered_candidate:
        score += SUBSTRING_BONUS
    if lowered_candidate.startswith(lowered_query):
        score += PREFIX_BONUS
    return score


def _match_bonus(
        query: str, candidate: str, query_index: int, found: int, previous_index: int) -> int:
    """單一字元命中的加分 / Bonus earned by a single character match."""
    bonus = 0
    if previous_index >= 0 and found == previous_index + 1:
        bonus += SEQUENTIAL_BONUS
    if found == 0 or candidate[found - 1] in WORD_SEPARATORS:
        bonus += WORD_BOUNDARY_BONUS
    if candidate[found] == query[query_index]:
        bonus += CASE_BONUS
    return bonus


def score_command(query: str, command: CommandEntry) -> int | None:
    """
    計算查詢字串對單一指令的分數
    Score ``query`` against a single :class:`CommandEntry`.

    標題的分數權重較高，但仍允許只比對到選單路徑的指令出現。
    The title is weighted higher, while a path-only match still qualifies.

    :param query: 使用者輸入的查詢字串 / The user supplied query
    :param command: 要評分的指令 / The command being scored
    :return: 分數，不相符時回傳 ``None`` / The score, or ``None`` when unmatched
    """
    title_score = fuzzy_score(query, command.title)
    path_score = fuzzy_score(query, command.search_text)
    if title_score is None and path_score is None:
        return None
    if title_score is None:
        return path_score
    if path_score is None:
        return title_score * TITLE_WEIGHT
    return max(title_score * TITLE_WEIGHT, path_score)


def rank_commands(
        query: str, commands: Iterable[CommandEntry],
        limit: int = DEFAULT_RESULT_LIMIT) -> list[CommandEntry]:
    """
    依模糊比對分數排序指令，最相符的排在前面
    Rank ``commands`` by fuzzy score, best match first.

    空查詢會依原本順序回傳前 ``limit`` 筆，讓面板一開啟就有內容。
    An empty query returns the first ``limit`` commands in their original order
    so the palette is never blank when it opens.

    :param query: 使用者輸入的查詢字串 / The user supplied query
    :param commands: 候選指令 / Candidate commands
    :param limit: 回傳筆數上限，非正數代表不限制 / Result cap; non-positive means no cap
    :return: 排序後的指令清單 / The ranked command list
    """
    command_list = list(commands)
    if not query.strip():
        return command_list[:limit] if limit > 0 else command_list

    scored: list[tuple[int, int, CommandEntry]] = []
    for index, command in enumerate(command_list):
        score = score_command(query, command)
        if score is not None:
            scored.append((score, index, command))

    # 以分數遞減排序，分數相同時保留原本順序（index 遞增）確保結果穩定
    # Sort by descending score, falling back to the original order for stability
    scored.sort(key=lambda item: (-item[0], item[1]))
    ranked = [command for _score, _index, command in scored]
    return ranked[:limit] if limit > 0 else ranked

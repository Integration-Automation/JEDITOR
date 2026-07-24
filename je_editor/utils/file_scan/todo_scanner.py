"""
掃描專案中的 TODO / FIXME 註解（純邏輯，不含 Qt）
Scan a project for TODO / FIXME comments (pure logic, no Qt imports).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from je_editor.utils.file_scan.file_indexer import index_project_files
from je_editor.utils.file_scan.ignore_rules import is_binary_file

# 預設掃描的標籤，取自業界常見的註解慣例
# Default tags, taken from the widely used comment conventions
DEFAULT_TAGS: tuple[str, ...] = ("TODO", "FIXME", "HACK", "XXX", "BUG", "NOTE", "OPTIMIZE")

# 註解起始符號，涵蓋 Python、C 系列、HTML、SQL、Lisp、LaTeX
# Comment openers covering Python, C-like, HTML, SQL, Lisp and LaTeX
COMMENT_MARKERS = r"(?:#|//|/\*|\*|<!--|--|;|%)"

# 單行讀取上限，避免壓縮過的單行檔案造成大量記憶體與回溯
# Per-line cap so a minified single-line file cannot blow up memory or backtracking
MAX_LINE_LENGTH = 500
# 掃描結果數量上限 / Cap on the number of reported items
DEFAULT_TODO_LIMIT = 5000


@dataclass(frozen=True)
class TodoItem:
    """
    一筆 TODO 註解
    One TODO-style comment.

    :param tag: 標籤名稱，例如 ``TODO`` / The tag name, e.g. ``TODO``
    :param message: 標籤後方的說明文字 / The text following the tag
    :param path: 專案相對路徑 / The project-relative path
    :param line: 1 起算的行號 / The 1-based line number
    """

    tag: str
    message: str
    path: str
    line: int


def build_tag_pattern(tags: Sequence[str] = DEFAULT_TAGS) -> re.Pattern:
    """
    建立比對 TODO 標籤的正規表示式
    Build the regular expression that matches TODO-style tags.

    標籤必須出現在註解符號之後，避免把一般字串誤判成待辦事項。
    A tag must follow a comment marker, so ordinary strings are not misreported.

    :param tags: 要比對的標籤 / The tags to match
    :return: 已編譯的樣式，群組 1 是標籤、群組 2 是說明文字
        / The compiled pattern; group 1 is the tag and group 2 the message
    """
    escaped = "|".join(re.escape(tag) for tag in tags if tag)
    if not escaped:
        # 沒有標籤時回傳永不相符的樣式，避免呼叫端需要另外處理 None
        # With no tags, return a never-matching pattern so callers need no None check.
        # ``\b\B`` can never hold at one position, so it matches nothing.
        return re.compile(r"\b\B")
    return re.compile(
        rf"{COMMENT_MARKERS}\s*\b({escaped})\b[:\s-]*(.*)",
        re.IGNORECASE,
    )


def scan_text(text: str, relative_path: str, pattern: re.Pattern) -> list[TodoItem]:
    """
    在單一檔案內容中尋找 TODO 註解
    Find TODO comments inside one file's text.

    :param text: 檔案內容 / The file text
    :param relative_path: 專案相對路徑 / The project-relative path
    :param pattern: :func:`build_tag_pattern` 產生的樣式 / A pattern from :func:`build_tag_pattern`
    :return: 找到的項目，依行號排列 / The items found, in line order
    """
    items: list[TodoItem] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        match = pattern.search(raw_line[:MAX_LINE_LENGTH])
        if match is None:
            continue
        items.append(
            TodoItem(
                tag=match.group(1).upper(),
                message=match.group(2).strip().rstrip("*/->").strip(),
                path=relative_path,
                line=line_number,
            )
        )
    return items


def scan_project_todos(
        root: str | Path,
        tags: Sequence[str] = DEFAULT_TAGS,
        should_stop: Callable[[], bool] | None = None,
        limit: int = DEFAULT_TODO_LIMIT) -> list[TodoItem]:
    """
    掃描整個專案並回傳所有 TODO 註解
    Scan a whole project and return every TODO-style comment.

    二進位檔與無法解碼的檔案會被略過，讓掃描在混合內容的專案中仍然安全。
    Binary and undecodable files are skipped so the scan stays safe in mixed trees.

    :param root: 專案根目錄 / The project root directory
    :param tags: 要比對的標籤 / The tags to match
    :param should_stop: 回傳 ``True`` 時提前中止，供背景執行緒取消用
        / Returning ``True`` aborts early, for cancellation from a worker thread
    :param limit: 回傳數量上限 / Cap on the number of returned items
    :return: 依檔案與行號排序的項目 / Items ordered by file then line
    """
    root_path = Path(root)
    pattern = build_tag_pattern(tags)
    found: list[TodoItem] = []
    for relative in index_project_files(root_path, should_stop=should_stop):
        if should_stop is not None and should_stop():
            break
        found.extend(_scan_one_file(root_path, relative, pattern))
        if len(found) >= limit:
            return found[:limit]
    return found


def _scan_one_file(root_path: Path, relative: str, pattern: re.Pattern) -> Iterable[TodoItem]:
    """讀取並掃描單一檔案 / Read and scan a single file."""
    full_path = root_path / relative
    if is_binary_file(full_path):
        return ()
    try:
        text = full_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ()
    return scan_text(text, relative, pattern)

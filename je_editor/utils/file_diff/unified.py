"""
產生「已提交版本 vs 編輯中內容」的 unified diff
Produce a unified diff of the committed version against the buffer.

輸出格式與 ``git diff`` 相同，因此既有的並排比對元件可以直接解析。
The output has the same shape as ``git diff``, so the existing side-by-side
viewer can parse it as-is. Pure logic: no Qt, no git.
"""
from __future__ import annotations

from difflib import unified_diff

# diff 標頭中代表「已提交版本」與「編輯中內容」的標籤
# Labels used in the diff header for the committed and edited sides
COMMITTED_LABEL = "HEAD"
WORKING_LABEL = "working copy"
# 變更前後保留的上下文行數，與 git 預設一致
# Context lines kept around a change, matching git's default
CONTEXT_LINES = 3


def unified_diff_text(
        baseline: str, current: str, file_name: str = "",
        context_lines: int = CONTEXT_LINES) -> str:
    """
    比較兩份內容並產生 unified diff
    Compare two texts and render a unified diff.

    :param baseline: 已提交的內容 / the committed content
    :param current: 編輯中的內容 / the buffer being edited
    :param file_name: 顯示在標頭的檔名 / the file name shown in the header
    :param context_lines: 保留的上下文行數 / how many context lines to keep
    :return: diff 文字；兩者相同時為空字串 / the diff, or an empty string when equal
    """
    if baseline == current:
        return ""
    from_label = f"a/{file_name} ({COMMITTED_LABEL})" if file_name else COMMITTED_LABEL
    to_label = f"b/{file_name} ({WORKING_LABEL})" if file_name else WORKING_LABEL
    lines = unified_diff(
        baseline.splitlines(keepends=True),
        current.splitlines(keepends=True),
        fromfile=from_label,
        tofile=to_label,
        n=context_lines,
    )
    return "".join(lines)

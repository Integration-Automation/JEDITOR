"""
解析 ruff 的 JSON 輸出成診斷清單
Turn ruff's JSON output into a list of diagnostics.

編輯器用這些診斷畫波浪底線並列在問題面板中。這裡是純邏輯：不執行 ruff、
不碰 Qt，因此可以用固定的輸出樣本測試。
The editor underlines these and lists them in the problems panel. Pure logic:
it neither runs ruff nor touches Qt, so it can be tested against fixed samples.

任何無法辨識的輸出都會被忽略而不是拋出例外——linter 的輸出格式改變不應該
讓編輯器壞掉。
Anything unrecognisable is skipped rather than raised: a change in the linter's
output must not break the editor.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

# ruff 對語法錯誤不會給規則代碼 / ruff reports no rule code for a syntax error
SYNTAX_ERROR_CODE = "SyntaxError"

# 嚴重度 / Severity levels
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

# ruff 規則代碼開頭對應的嚴重度；其餘視為提示
# What each ruff rule-code prefix means; anything else counts as a hint
_SEVERITY_BY_PREFIX = {
    "E": SEVERITY_ERROR,  # pycodestyle errors
    "F": SEVERITY_ERROR,  # pyflakes
    "W": SEVERITY_WARNING,  # pycodestyle warnings
    "C": SEVERITY_WARNING,  # complexity
    "B": SEVERITY_WARNING,  # bugbear
    "S": SEVERITY_WARNING,  # security
}

# LSP 的嚴重度編號 / The numbers LSP uses for severity
_LSP_SEVERITY = {1: SEVERITY_ERROR, 2: SEVERITY_WARNING, 3: SEVERITY_INFO, 4: SEVERITY_INFO}


def severity_for_code(code: str) -> str:
    """
    由規則代碼推出嚴重度
    Work out a severity from a rule code.

    :param code: 規則代碼，例如 ``F401`` / the rule code, such as ``F401``
    :return: 嚴重度 / the severity
    """
    if not code or code == SYNTAX_ERROR_CODE:
        return SEVERITY_ERROR
    return _SEVERITY_BY_PREFIX.get(code[0].upper(), SEVERITY_INFO)


@dataclass(frozen=True)
class Diagnostic:
    """
    一筆 linter 診斷
    One linter finding.

    :param line: 起始行（1 起算，與 ruff 一致）/ start line, 1-based as ruff reports
    :param column: 起始欄（1 起算）/ start column, 1-based
    :param end_line: 結束行 / end line
    :param end_column: 結束欄 / end column
    :param code: 規則代碼，例如 ``F401`` / the rule code, e.g. ``F401``
    :param message: 說明文字 / the human-readable message
    :param severity: 嚴重度，未給時由代碼推出 / the severity, derived from the code
        when not given
    :param file_path: 所屬檔案；只檢查目前緩衝區時為空
        the file it belongs to, empty when only the current buffer was checked
    """

    line: int
    column: int
    end_line: int
    end_column: int
    code: str
    message: str
    severity: str = ""
    file_path: str = ""

    @property
    def label(self) -> str:
        """給面板顯示的一行說明 / A single line for the panel."""
        return f"{self.code} {self.message}" if self.code else self.message

    @property
    def level(self) -> str:
        """嚴重度；沒有明講時由規則代碼推出 / The severity, derived from the code if unset."""
        return self.severity or severity_for_code(self.code)


def _as_position(raw: object, fallback_row: int, fallback_column: int) -> tuple[int, int]:
    """讀出 ``{"row": n, "column": n}``，缺漏時退回預設 / Read a position, with fallbacks."""
    if not isinstance(raw, dict):
        return fallback_row, fallback_column
    row = raw.get("row")
    column = raw.get("column")
    return (
        row if isinstance(row, int) and row > 0 else fallback_row,
        column if isinstance(column, int) and column > 0 else fallback_column,
    )


def _as_diagnostic(entry: object) -> Diagnostic | None:
    """把一筆 ruff 記錄轉成診斷，無法辨識時回傳 ``None`` / Convert one ruff record."""
    if not isinstance(entry, dict):
        return None
    message = entry.get("message")
    if not isinstance(message, str) or not message:
        return None
    line, column = _as_position(entry.get("location"), 1, 1)
    end_line, end_column = _as_position(entry.get("end_location"), line, column)
    code = entry.get("code")
    return Diagnostic(
        line=line,
        column=column,
        # 結束位置若在起始之前（輸出有誤）就退回起始位置
        # An end before the start (malformed output) falls back to the start
        end_line=max(end_line, line),
        end_column=end_column,
        code=code if isinstance(code, str) else SYNTAX_ERROR_CODE,
        message=message,
        file_path=str(entry.get("filename") or ""),
    )


def parse_ruff_json(output: str) -> list[Diagnostic]:
    """
    解析 ruff ``--output-format json`` 的輸出
    Parse the output of ruff's ``--output-format json``.

    :param output: ruff 的標準輸出 / ruff's standard output
    :return: 診斷清單；輸出為空或無法解析時為空清單
        the diagnostics, or an empty list when the output is empty or unusable
    """
    if not output.strip():
        return []
    try:
        entries = json.loads(output)
    except ValueError:
        return []
    if not isinstance(entries, list):
        return []
    diagnostics = [_as_diagnostic(entry) for entry in entries]
    return [diagnostic for diagnostic in diagnostics if diagnostic is not None]


def diagnostic_from_entry(entry: dict) -> Diagnostic | None:
    """
    把其他來源的診斷轉成同一種形式
    Convert a diagnostic from another source into the same shape.

    語言伺服器回報的診斷與 ruff 的欄位不同，但編輯器只認得一種形式；統一之後
    底線與問題面板就不必分辨診斷是誰報的。
    A language server reports different fields from ruff, but the editor knows
    only one shape. Converting here means the underlines and the problems panel
    never have to care which tool produced a finding.

    :param entry: 來源診斷，需含 ``line`` 與 ``message`` / the source diagnostic
    :return: 統一形式的診斷，資料不足時為 ``None`` / the diagnostic, or ``None``
    """
    if not isinstance(entry, dict):
        return None
    message = entry.get("message")
    line = entry.get("line")
    if not isinstance(message, str) or not message:
        return None
    if not isinstance(line, int) or line < 1:
        return None
    column = entry.get("column")
    column = column if isinstance(column, int) and column >= 1 else 1
    end_line = entry.get("end_line")
    end_line = end_line if isinstance(end_line, int) and end_line >= line else line
    end_column = entry.get("end_column")
    end_column = end_column if isinstance(end_column, int) and end_column >= 1 else column
    code = entry.get("code")
    severity = entry.get("severity")
    return Diagnostic(
        line=line, column=column, end_line=end_line, end_column=end_column,
        code=code if isinstance(code, str) and code else SYNTAX_ERROR_CODE,
        message=message,
        severity=_LSP_SEVERITY.get(severity, "") if isinstance(severity, int) else "",
        file_path=str(entry.get("file_path") or ""))


def diagnostics_from_entries(entries: list) -> list[Diagnostic]:
    """
    批次轉換其他來源的診斷
    Convert a batch of diagnostics from another source.

    :param entries: 來源診斷清單 / the source diagnostics
    :return: 可用的診斷 / the usable diagnostics
    """
    if not isinstance(entries, list):
        return []
    converted = [diagnostic_from_entry(entry) for entry in entries]
    return [item for item in converted if item is not None]


def diagnostics_by_line(diagnostics: list[Diagnostic]) -> dict[int, list[Diagnostic]]:
    """
    依行號分組
    Group diagnostics by their starting line.

    :param diagnostics: 診斷清單 / the diagnostics to group
    :return: 行號（1 起算）對應該行的診斷 / 1-based line number -> its diagnostics
    """
    grouped: dict[int, list[Diagnostic]] = {}
    for diagnostic in diagnostics:
        grouped.setdefault(diagnostic.line, []).append(diagnostic)
    return grouped


def message_for_line(diagnostics: list[Diagnostic], line: int) -> str | None:
    """
    取得某行的診斷說明（多筆以換行分隔）
    Return the messages reported on *line*, one per line of text.

    :param diagnostics: 診斷清單 / the diagnostics to search
    :param line: 1 起算的行號 / the 1-based line number
    :return: 說明文字，該行沒有診斷時為 ``None`` / the text, or ``None``
    """
    on_line = [item.label for item in diagnostics if item.line == line]
    return "\n".join(on_line) if on_line else None

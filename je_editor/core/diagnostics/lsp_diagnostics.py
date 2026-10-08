"""
把語言伺服器回報的診斷轉成統一模型
Convert what a language server reports into the unified model.

``utils/lsp/lsp_protocol.diagnostic_entries`` 已經把 ``publishDiagnostics`` 讀成
行列 1 起算的字典；這裡把那些字典變成 :class:`Diagnostic`，嚴重度與來源都保留。
``utils/lsp/lsp_protocol.diagnostic_entries`` already reads ``publishDiagnostics``
into dictionaries with 1-based lines and columns. This turns those dictionaries
into :class:`Diagnostic` objects, keeping the severity and the source.
"""
from __future__ import annotations

from je_editor.core.diagnostics.diagnostic_model import Diagnostic, Severity, TextRange

# LSP 規定沒給嚴重度時由用戶端決定；當成錯誤才不會被篩選器藏起來
# LSP leaves a missing severity to the client; calling it an error keeps a filter
# from hiding it
DEFAULT_SEVERITY = Severity.ERROR


def _severity(raw: object) -> Severity:
    """讀出嚴重度，不認得時用預設 / Read a severity, falling back when unrecognised."""
    if isinstance(raw, int) and not isinstance(raw, bool) and raw in tuple(Severity):
        return Severity(raw)
    return DEFAULT_SEVERITY


def from_lsp_entry(entry: object, uri: str = "", default_source: str = "") -> Diagnostic | None:
    """
    把一筆語言伺服器的診斷轉成統一模型
    Convert one language-server diagnostic into the unified model.

    :param entry: ``diagnostic_entries`` 給的一筆字典 / one dictionary from
        ``diagnostic_entries``
    :param uri: 診斷所在的資源 / the resource the diagnostic is in
    :param default_source: 伺服器沒有說明來源時使用的名稱，通常是伺服器的名稱
        the name to use when the server names no source, usually the server's own
    :return: 診斷；資料不足（沒有訊息或行號）時為 ``None``
        the diagnostic, or ``None`` when the message or the line is missing
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
    end_line = entry.get("end_line")
    end_column = entry.get("end_column")
    code = entry.get("code")
    source = entry.get("source")
    return Diagnostic(
        message=message,
        range=TextRange.from_lines(
            line,
            column if isinstance(column, int) else 1,
            end_line if isinstance(end_line, int) else None,
            end_column if isinstance(end_column, int) else None),
        severity=_severity(entry.get("severity")),
        source=source if isinstance(source, str) and source else default_source,
        code=code if isinstance(code, str) else "",
        uri=uri,
    )


def from_lsp_entries(entries: object, uri: str = "", default_source: str = "") -> list[Diagnostic]:
    """
    批次轉換語言伺服器的診斷
    Convert a batch of language-server diagnostics.

    :param entries: ``diagnostic_entries`` 的結果 / what ``diagnostic_entries`` returned
    :param uri: 診斷所在的資源 / the resource the diagnostics are in
    :param default_source: 伺服器沒有說明來源時使用的名稱
        the name to use when the server names no source
    :return: 可用的診斷 / the usable diagnostics
    """
    if not isinstance(entries, list):
        return []
    converted = [from_lsp_entry(entry, uri, default_source) for entry in entries]
    return [item for item in converted if item is not None]

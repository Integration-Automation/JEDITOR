"""
舊診斷形式與統一模型之間的轉換
Conversion between the older diagnostic shape and the unified model.

編輯器的底線、縮圖與問題面板目前都吃 ``utils/lint`` 的 ``Diagnostic``。在它們
逐一改用統一模型之前，這裡讓兩邊可以互轉，兩種形式就不必同時改。
The editor's underlines, minimap and problems panel all take the ``Diagnostic``
from ``utils/lint`` today. Until each of them moves to the unified model, this
converts both ways so the two shapes need not change at once.
"""
from __future__ import annotations

from je_editor.core.diagnostics.diagnostic_model import Diagnostic, Severity, TextRange
from je_editor.core.uri.resource_uri import to_path, to_uri
from je_editor.utils.lint.ruff_diagnostics import (
    SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_WARNING
)
from je_editor.utils.lint.ruff_diagnostics import Diagnostic as LegacyDiagnostic

# 舊形式的嚴重度字串對應的嚴重度 / The severity each older severity string means
_SEVERITY_FROM_LEGACY = {
    SEVERITY_ERROR: Severity.ERROR,
    SEVERITY_WARNING: Severity.WARNING,
    SEVERITY_INFO: Severity.INFORMATION,
}

# 舊形式沒有「提示」這一級，併入資訊 / The older shape has no hint level, so it joins information
_LEGACY_FROM_SEVERITY = {
    Severity.ERROR: SEVERITY_ERROR,
    Severity.WARNING: SEVERITY_WARNING,
    Severity.INFORMATION: SEVERITY_INFO,
    Severity.HINT: SEVERITY_INFO,
}


def from_legacy(diagnostic: LegacyDiagnostic, source: str, uri: str = "") -> Diagnostic:
    """
    把舊形式的診斷轉成統一模型
    Convert an older diagnostic into the unified model.

    :param diagnostic: 舊形式的診斷 / the older diagnostic
    :param source: 誰報的；舊形式沒有記這件事 / who reported it, which the older
        shape does not record
    :param uri: 所在資源的 URI；舊診斷自己帶著檔案路徑時以它為準
        the resource's URI; a file path the older diagnostic carries wins over it
    :return: 統一模型的診斷 / the diagnostic in the unified model
    """
    return Diagnostic(
        message=diagnostic.message,
        range=TextRange.from_lines(
            diagnostic.line, diagnostic.column, diagnostic.end_line, diagnostic.end_column),
        severity=_SEVERITY_FROM_LEGACY.get(diagnostic.level, Severity.INFORMATION),
        source=source,
        code=diagnostic.code,
        uri=to_uri(diagnostic.file_path) if diagnostic.file_path else uri,
    )


def to_legacy(diagnostic: Diagnostic) -> LegacyDiagnostic:
    """
    把統一模型的診斷轉回舊形式
    Convert a unified diagnostic back into the older shape.

    來源、相關位置與修正在舊形式裡沒有位置，會被丟掉。
    The source, the related locations and the fixes have no place in the older
    shape and are dropped.

    :param diagnostic: 統一模型的診斷 / the diagnostic in the unified model
    :return: 舊形式的診斷 / the older diagnostic
    """
    return LegacyDiagnostic(
        line=diagnostic.range.start.line,
        column=diagnostic.range.start.column,
        end_line=diagnostic.range.end.line,
        end_column=diagnostic.range.end.column,
        code=diagnostic.code,
        message=diagnostic.message,
        severity=_LEGACY_FROM_SEVERITY[diagnostic.severity],
        file_path=to_path(diagnostic.uri),
    )

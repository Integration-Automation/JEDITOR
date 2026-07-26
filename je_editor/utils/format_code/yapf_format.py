"""
用 yapf 格式化 Python 程式碼
Format Python source with yapf.

格式化本身是純文字轉換，抽出來之後選單動作與「存檔時自動格式化」可以共用同
一份邏輯，也能單獨測試。
Formatting is a plain text-to-text transform. Extracting it lets the menu action
and format-on-save share one implementation, and makes it testable on its own.
"""
from __future__ import annotations

from yapf.yapflib.errors import YapfError
from yapf.yapflib.yapf_api import FormatCode

from je_editor.utils.logging.loggin_instance import jeditor_logger

# 預設的 yapf 風格 / The yapf style used by default
DEFAULT_STYLE = "google"


def format_python_source(source: str, style: str = DEFAULT_STYLE) -> str:
    """
    格式化 Python 原始碼
    Reformat Python source.

    語法錯誤的程式碼無法格式化，這時回傳原內容而不是拋出例外——存檔時自動格式化
    絕不能因為程式碼還沒寫完就中斷存檔。yapf 對語法錯誤丟的是自己的 ``YapfError``
    而不是 ``SyntaxError``，兩者都要接。
    Source with a syntax error cannot be formatted; the original is returned
    rather than raising, because format-on-save must never block a save just
    because the code is still half-written. yapf raises its own ``YapfError``
    for a syntax error rather than ``SyntaxError``, so both are caught.

    :param source: 原始碼 / the source to format
    :param style: yapf 風格名稱 / the yapf style to apply
    :return: 格式化後的原始碼；無法格式化時為原內容
        the formatted source, or the original when it cannot be formatted
    """
    if not source.strip():
        return source
    try:
        formatted, _changed = FormatCode(unformatted_source=source, style_config=style)
    except (YapfError, SyntaxError, ValueError, IndentationError, UnicodeDecodeError) as error:
        jeditor_logger.debug(f"yapf_format: source was not formatted: {error!r}")
        return source
    return formatted if isinstance(formatted, str) else source

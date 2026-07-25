"""
用括號或引號包住選取的文字
Wrap a selection in brackets or quotes.

純文字轉換，插入與游標處理留給編輯器。
A plain text transform; inserting it and moving the caret is the editor's job.
"""
from __future__ import annotations

# 開頭字元對應的結尾字元 / The closing character for each opening one
SURROUND_PAIRS = {
    "(": ")",
    "[": "]",
    "{": "}",
    "<": ">",
    "'": "'",
    '"': '"',
    "`": "`",
}


def closing_for(opening: str) -> str | None:
    """
    取得對應的結尾字元
    The closing character that matches an opening one.

    :param opening: 開頭字元 / the opening character
    :return: 結尾字元，不成對時為 ``None`` / the closing one, or ``None``
    """
    return SURROUND_PAIRS.get(opening)


def surround(text: str, opening: str) -> str | None:
    """
    把文字包在成對的字元之間
    Put text between a matching pair of characters.

    :param text: 要包住的文字 / the text to wrap
    :param opening: 開頭字元 / the opening character
    :return: 包好的文字；字元不成對時為 ``None`` / the wrapped text, or ``None``
    """
    closing = closing_for(opening)
    if closing is None:
        return None
    return f"{opening}{text}{closing}"

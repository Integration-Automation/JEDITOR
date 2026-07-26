"""
處理文字檔的編碼與行尾
Handle a text file's encoding and line endings.

編輯器內部一律以 ``\\n`` 表示換行（Qt 文件就是這樣），因此讀進來要正規化、
寫出去要換回檔案原本的行尾，否則存一次檔就會把整份檔案的行尾都改掉。
The editor always uses ``\\n`` internally, as a Qt document does, so text is
normalised on the way in and converted back on the way out — otherwise a single
save would rewrite every line ending in the file.

純邏輯：不碰 Qt，也不做檔案 I/O。
Pure logic: no Qt and no file I/O.
"""
from __future__ import annotations

import codecs

# 行尾種類 / The line-ending styles
LINE_ENDING_LF = "\n"
LINE_ENDING_CRLF = "\r\n"
LINE_ENDING_CR = "\r"

# 顯示名稱對應 / Display name for each style
LINE_ENDING_NAMES = {
    LINE_ENDING_LF: "LF",
    LINE_ENDING_CRLF: "CRLF",
    LINE_ENDING_CR: "CR",
}

# 預設編碼 / The encoding assumed when nothing else is known
DEFAULT_ENCODING = "utf-8"

# BOM 與對應編碼；順序重要，UTF-32 的 BOM 開頭與 UTF-16 相同
# Byte-order marks and their encodings. Order matters: a UTF-32 BOM starts with
# the same two bytes as a UTF-16 one.
_BOM_ENCODINGS = (
    (codecs.BOM_UTF8, "utf-8-sig"),
    (codecs.BOM_UTF32_LE, "utf-32"),
    (codecs.BOM_UTF32_BE, "utf-32"),
    (codecs.BOM_UTF16_LE, "utf-16"),
    (codecs.BOM_UTF16_BE, "utf-16"),
)


def detect_line_ending(text: str) -> str:
    """
    判斷文字使用的行尾
    Work out which line ending a text uses.

    以出現次數最多的為準；沒有任何換行時視為 ``LF``。
    The most common one wins; a text with no line break at all counts as ``LF``.

    :param text: 要判斷的文字 / the text to inspect
    :return: 行尾字串 / the line-ending string
    """
    crlf = text.count(LINE_ENDING_CRLF)
    # 單獨的 CR 與 LF 不能把 CRLF 算進去 / Lone CR and LF must not count CRLF twice
    lone_cr = text.count(LINE_ENDING_CR) - crlf
    lone_lf = text.count(LINE_ENDING_LF) - crlf
    if crlf >= lone_lf and crlf >= lone_cr and crlf > 0:
        return LINE_ENDING_CRLF
    if lone_cr > lone_lf:
        return LINE_ENDING_CR
    return LINE_ENDING_LF


def line_ending_name(ending: str) -> str:
    """
    取得行尾的顯示名稱
    The display name of a line ending.

    :param ending: 行尾字串 / the line-ending string
    :return: 名稱，未知時回傳 ``LF`` / its name, defaulting to ``LF``
    """
    return LINE_ENDING_NAMES.get(ending, LINE_ENDING_NAMES[LINE_ENDING_LF])


def normalise_line_endings(text: str) -> str:
    """
    把所有行尾正規化為 ``\\n``
    Normalise every line ending to ``\\n``.

    :param text: 原始文字 / the original text
    :return: 正規化後的文字 / the normalised text
    """
    return text.replace(LINE_ENDING_CRLF, LINE_ENDING_LF).replace(
        LINE_ENDING_CR, LINE_ENDING_LF)


def apply_line_ending(text: str, ending: str) -> str:
    """
    把文字的行尾換成指定樣式
    Convert a text's line endings to *ending*.

    :param text: 要轉換的文字（任何行尾）/ the text to convert, in any style
    :param ending: 目標行尾 / the line ending to write
    :return: 轉換後的文字 / the converted text
    """
    normalised = normalise_line_endings(text)
    if ending == LINE_ENDING_LF:
        return normalised
    return normalised.replace(LINE_ENDING_LF, ending)


def encoding_from_bom(raw: bytes) -> str | None:
    """
    由 BOM 判斷編碼
    Work out an encoding from a byte-order mark.

    :param raw: 檔案開頭的位元組 / the file's leading bytes
    :return: 編碼名稱，沒有 BOM 時為 ``None`` / the encoding, or ``None``
    """
    for bom, encoding in _BOM_ENCODINGS:
        if raw.startswith(bom):
            return encoding
    return None


def decode_bytes(raw: bytes, encoding: str | None = None) -> tuple[str, str]:
    """
    解碼檔案內容，並回報實際使用的編碼
    Decode a file's bytes, reporting which encoding actually worked.

    指定編碼時就用它；沒有指定時先看 BOM，再試 UTF-8，最後退回 latin-1——
    latin-1 不會失敗，因此檔案至少能開起來讓使用者自己選正確的編碼。
    An explicit encoding is used as given. Otherwise a BOM decides, then UTF-8 is
    tried, and latin-1 is the fallback: it cannot fail, so the file always opens
    and the user can pick the right encoding themselves.

    :param raw: 檔案內容 / the file's bytes
    :param encoding: 指定的編碼，``None`` 表示自動判斷 / the encoding, or ``None`` to detect
    :return: ``(文字, 使用的編碼)`` / ``(text, encoding used)``
    :raises UnicodeDecodeError: 指定的編碼無法解碼時 / when an explicit encoding fails
    """
    if encoding is not None:
        return raw.decode(encoding), encoding
    from_bom = encoding_from_bom(raw)
    if from_bom is not None:
        return raw.decode(from_bom), from_bom
    try:
        return raw.decode(DEFAULT_ENCODING), DEFAULT_ENCODING
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1"

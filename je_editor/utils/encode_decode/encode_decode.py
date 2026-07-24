"""
文字編碼／解碼工具（純邏輯，不含 Qt）
Text encode/decode helpers (pure logic, no Qt imports).

解碼失敗時一律回傳 ``None``，讓 UI 層可以安全地「不做任何改動」而非拋出例外。
Decoders return ``None`` on failure, so the UI layer can safely leave the text
unchanged instead of raising.
"""
from __future__ import annotations

import base64
import binascii
import html
import json
from urllib.parse import quote, unquote

# base64 / URL 一律以 UTF-8 處理位元組 / Bytes are handled as UTF-8 throughout
_ENCODING = "utf-8"


def base64_encode(text: str) -> str:
    """
    將文字以 Base64 編碼
    Encode text as Base64.

    :param text: 原始文字 / The original text
    :return: Base64 字串 / The Base64 string
    """
    return base64.b64encode(text.encode(_ENCODING)).decode("ascii")


def base64_decode(text: str) -> str | None:
    """
    將 Base64 字串解碼回文字
    Decode a Base64 string back into text.

    輸入不是合法的 Base64、或解出來不是有效 UTF-8 時回傳 ``None``。
    Returns ``None`` when the input is not valid Base64 or does not decode as UTF-8.

    :param text: Base64 字串 / The Base64 string
    :return: 解碼後的文字，失敗時回傳 ``None`` / The decoded text, or ``None`` on failure
    """
    try:
        decoded = base64.b64decode(text.strip(), validate=True)
        return decoded.decode(_ENCODING)
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return None


def url_encode(text: str) -> str:
    """
    將文字做 URL 百分比編碼
    Percent-encode text for use in a URL.

    :param text: 原始文字 / The original text
    :return: URL 編碼後的字串 / The percent-encoded string
    """
    return quote(text, safe="")


def url_decode(text: str) -> str:
    """
    將 URL 百分比編碼還原為文字
    Decode percent-encoded text back to plain text.

    :param text: URL 編碼字串 / The percent-encoded string
    :return: 還原後的文字 / The decoded text
    """
    return unquote(text)


def html_escape(text: str) -> str:
    """
    將文字中的 HTML 特殊字元轉為實體
    Escape HTML-special characters into entities.

    :param text: 原始文字 / The original text
    :return: 轉義後的文字 / The escaped text
    """
    return html.escape(text)


def html_unescape(text: str) -> str:
    """
    將 HTML 實體還原為原始字元
    Unescape HTML entities back into characters.

    :param text: 含實體的文字 / Text containing entities
    :return: 還原後的文字 / The unescaped text
    """
    return html.unescape(text)


def json_string_escape(text: str) -> str:
    """
    把文字轉成合法的 JSON 字串字面值（含引號）
    Turn text into a valid JSON string literal (including the surrounding quotes).

    :param text: 原始文字 / The original text
    :return: JSON 字串字面值，例如 ``"a\\nb"`` / A JSON string literal, e.g. ``"a\\nb"``
    """
    return json.dumps(text)


def json_string_unescape(text: str) -> str | None:
    """
    把 JSON 字串字面值還原為原始文字
    Turn a JSON string literal back into its raw text.

    輸入不是合法的 JSON 字串（例如缺少引號或跳脫錯誤）時回傳 ``None``。
    Returns ``None`` when the input is not a valid JSON string (missing quotes,
    bad escapes, or not a string).

    :param text: JSON 字串字面值 / A JSON string literal
    :return: 還原後的文字，失敗時回傳 ``None`` / The raw text, or ``None`` on failure
    """
    try:
        parsed = json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        return None
    return parsed if isinstance(parsed, str) else None

"""
把系統語系對應到編輯器支援的語言
Match the system's locale to a language the editor speaks.

第一次啟動時沒有任何語言設定，與其一律給英文，不如照系統語系挑一個——使用者的系
統已經說明了他讀哪種語言。
On a first run there is no language setting, and rather than always falling back
to English it is better to follow the system: it already says which language the
user reads.

純邏輯，不含 Qt，因此可以直接餵語系字串測試。
Pure logic with no Qt, so it can be tested by feeding it locale strings.
"""
from __future__ import annotations

from typing import Dict, Optional

# 預設語言 / The language assumed when nothing matches
DEFAULT_LANGUAGE = "English"

# 語系前綴對應的語言；中文另外處理，因為要分繁簡
# The language for each locale prefix. Chinese is handled separately, since the
# script matters more than the country does.
_LANGUAGE_BY_PREFIX: Dict[str, str] = {
    "en": "English",
    "ja": "Japanese",
    "ko": "Korean",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "pt": "Portuguese",
}

# 使用繁體字的中文語系 / The Chinese locales written in traditional characters
_TRADITIONAL_REGIONS = frozenset({"tw", "hk", "mo"})
# 明確標示字集的寫法，例如 ``zh-Hant`` / Explicit script tags such as ``zh-Hant``
_TRADITIONAL_SCRIPTS = frozenset({"hant", "traditional"})
_SIMPLIFIED_SCRIPTS = frozenset({"hans", "simplified"})


def normalise_locale(locale_name: str | None) -> list[str]:
    """
    把語系字串拆成小寫的組成部分
    Split a locale string into its lower-cased parts.

    可能拿到 ``zh_TW``、``zh-Hant-TW``、``zh_TW.UTF-8`` 等寫法，全部一視同仁。
    It may arrive as ``zh_TW``, ``zh-Hant-TW`` or ``zh_TW.UTF-8``, and all of
    those are treated alike.

    :param locale_name: 系統回報的語系 / the locale the system reported
    :return: 小寫的組成部分 / its parts, lower-cased
    """
    text = str(locale_name or "").strip().split(".")[0]
    return [part for part in text.replace("-", "_").lower().split("_") if part]


def language_for_locale(locale_name: str | None,
                        available: Optional[set] = None) -> str:
    """
    取得語系對應的語言
    The language a locale should get.

    中文依字集決定：``zh-Hant``、``zh_TW``、``zh_HK``、``zh_MO`` 用繁體，其餘用
    簡體。認不得的語系用英文。
    Chinese follows its script: ``zh-Hant``, ``zh_TW``, ``zh_HK`` and ``zh_MO``
    get traditional characters and anything else simplified. An unrecognised
    locale gets English.

    :param locale_name: 系統回報的語系 / the locale the system reported
    :param available: 目前有哪些語言可用；省略時不檢查
        / which languages exist, or ``None`` to skip the check
    :return: 語言名稱 / the language's name
    """
    parts = normalise_locale(locale_name)
    if not parts:
        return DEFAULT_LANGUAGE
    chosen = _chinese_variant(parts) if parts[0] == "zh" else _LANGUAGE_BY_PREFIX.get(parts[0])
    if chosen is None:
        return DEFAULT_LANGUAGE
    if available is not None and chosen not in available:
        return DEFAULT_LANGUAGE
    return chosen


def _chinese_variant(parts: list[str]) -> str:
    """判斷中文語系該用繁體還是簡體 / Whether a Chinese locale is traditional or simplified."""
    for part in parts[1:]:
        if part in _TRADITIONAL_SCRIPTS or part in _TRADITIONAL_REGIONS:
            return "Traditional_Chinese"
        if part in _SIMPLIFIED_SCRIPTS:
            return "Simplified_Chinese"
    # 只寫 ``zh`` 時視為簡體：那是使用人數最多的一邊
    # A bare ``zh`` counts as simplified, which is the larger readership
    return "Simplified_Chinese"


def system_locale_name() -> str:
    """
    取得系統目前的語系
    The locale the system is currently set to.

    先問 Qt，因為它在 Windows 上讀的是使用者的顯示語言，比環境變數可靠；Qt 不在時
    退回標準函式庫。
    Qt is asked first: on Windows it reads the user's display language, which is
    more reliable than the environment variables. Without Qt the standard library
    answers instead.

    :return: 語系名稱，取不到時為空字串 / the locale, or an empty string
    """
    try:
        from PySide6.QtCore import QLocale
        return QLocale.system().name()
    except ImportError:
        import locale
        return locale.getdefaultlocale()[0] or ""

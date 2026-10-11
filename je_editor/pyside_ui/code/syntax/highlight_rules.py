"""
以正規表示式寫成的高亮規則，各個高亮器共用
Highlight rules written as regular expressions, shared by every highlighter.

插件以「副檔名加一組關鍵字」來擴充高亮，這套規則要疊在任何一種高亮器之上都一樣
生效，所以從 Python 的高亮器裡搬出來放在這裡。
A plugin extends highlighting with a suffix and a set of keywords, and those
rules have to work the same on top of whichever highlighter is in use, so they
were moved out of the Python highlighter into this module.
"""
from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat

from je_editor.pyside_ui.code.syntax.syntax_setting import syntax_extend_setting_dict
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict

HighlightRule = tuple[QRegularExpression, QTextCharFormat]


def make_format(color: object) -> QTextCharFormat:
    """
    建立含前景色的格式
    Build a format with the given foreground.

    顏色可以是主題顏色的鍵（內建規則都是這種），也可以是直接給的 QColor（插件沿用
    的寫法）。
    The colour may be a theme colour key, as every built-in rule uses, or a
    QColor given directly, which is what plugins do.

    :param color: 主題顏色的鍵或 QColor / a theme colour key or a QColor
    :return: 格式；鍵不存在時沒有前景色 / the format, without a foreground when the
        key is unknown
    """
    text_format = QTextCharFormat()
    if isinstance(color, str):
        themed = actually_color_dict.get(color)
        if themed is not None:
            text_format.setForeground(themed)
        return text_format
    text_format.setForeground(color)
    return text_format


def regex_rules(rule_setting: dict) -> list[HighlightRule]:
    """
    把一組「正則規則」設定變成規則
    Turn a group of regex rule settings into rules.

    :param rule_setting: ``{名稱: {"rules": (...), "color": ...}}``
        ``{name: {"rules": (...), "color": ...}}``
    :return: 規則清單 / the rules
    """
    found: list[HighlightRule] = []
    for setting in rule_setting.values():
        text_format = make_format(setting.get("color"))
        found.extend((QRegularExpression(rule), text_format) for rule in setting.get("rules", ()))
    return found


def word_rules(word_setting: dict) -> list[HighlightRule]:
    """
    把一組「關鍵字」設定變成整字比對的規則
    Turn a group of keyword settings into whole-word rules.

    :param word_setting: ``{名稱: {"words": (...), "color": ...}}``
        ``{name: {"words": (...), "color": ...}}``
    :return: 規則清單 / the rules
    """
    found: list[HighlightRule] = []
    for setting in word_setting.values():
        text_format = make_format(setting.get("color"))
        found.extend((QRegularExpression(rf"\b{word}\b"), text_format)
                     for word in setting.get("words", ()))
    return found


def plugin_rules(suffix: str) -> list[HighlightRule]:
    """
    取得插件為某個副檔名登記的規則
    The rules plugins registered for a file suffix.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 規則清單，沒有插件登記時為空 / the rules, none when no plugin registered any
    """
    from je_editor.plugins import get_programming_language_plugin

    plugin = get_programming_language_plugin(suffix)
    if plugin:
        return regex_rules(plugin.get("syntax_rules", {})) + word_rules(plugin.get("syntax_words", {}))
    # 向後相容：直接寫進 syntax_extend_setting_dict 的舊寫法
    # Backward compatible: the old way of writing into syntax_extend_setting_dict directly
    legacy = syntax_extend_setting_dict.get(suffix)
    return word_rules(legacy) if legacy else []


def apply_rules(highlighter: QSyntaxHighlighter, text: str, rules: list[HighlightRule]) -> None:
    """
    把規則套用到高亮器正在處理的那一行
    Apply rules to the line a highlighter is working on.

    :param highlighter: 正在處理一行的高亮器 / the highlighter, in the middle of a line
    :param text: 那一行的文字 / the text of that line
    :param rules: 要套用的規則，後面的蓋過前面的 / the rules, later ones over earlier ones
    """
    for pattern, text_format in rules:
        matches = pattern.globalMatch(text)
        while matches.hasNext():
            match = matches.next()
            highlighter.setFormat(match.capturedStart(), match.capturedLength(), text_format)


def release_document(highlighter: QSyntaxHighlighter) -> None:
    """
    把高亮器從文件上拿掉，而不讓文件以為自己被編輯了
    Take a highlighter off its document without the document looking edited.

    拿掉高亮器時 Qt 會清掉它畫的顏色，並為此送出「內容變了」的訊號；聽那個訊號的
    人（例如分頁的未儲存標記）分不出這跟真正的編輯有什麼不同，所以這段期間先把
    文件的訊號擋住。版面是直接被通知的，不靠訊號，畫面照樣會更新。
    Qt clears the colours a highlighter painted when it is taken off, and sends
    the content-changed signal for it. Whoever listens, the tab's unsaved mark
    for one, cannot tell that from a real edit, so the document's signals are
    held back meanwhile. The layout is told directly rather than by signal, and
    the view still updates.

    :param highlighter: 要拿掉的高亮器 / the highlighter to take off
    """
    document = highlighter.document()
    if document is None:
        return
    was_blocked = document.blockSignals(True)
    try:
        highlighter.setDocument(None)
    finally:
        document.blockSignals(was_blocked)

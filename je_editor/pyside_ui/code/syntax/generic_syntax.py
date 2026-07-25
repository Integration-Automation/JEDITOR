"""
以關鍵字規則為基礎的通用語法高亮
Keyword-driven highlighting for languages other than Python.

Python 由專屬的高亮器處理；其他語言以「關鍵字、字串、註解、數字」四類上色，
雖然比不上真正的語法分析，但足以讓程式碼結構一眼可辨。
Python has a highlighter of its own. Everything else is coloured in four
categories — keywords, strings, comments and numbers — which is short of real
parsing but enough to make the shape of the code readable.
"""
from __future__ import annotations

import re

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QTextDocument

from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.syntax.language_rules import LanguageRules, rules_for

# 區塊註解的狀態值 / The block state marking "inside a block comment"
_INSIDE_BLOCK_COMMENT = 1


def _format_for(colour_key: str) -> QTextCharFormat:
    """建立指定顏色的格式 / Build a format in the given colour."""
    text_format = QTextCharFormat()
    text_format.setForeground(actually_color_dict.get(colour_key))
    return text_format


class GenericHighlighter(QSyntaxHighlighter):
    """
    依語言規則上色的通用高亮器
    A highlighter that colours a document from a language's rules.
    """

    def __init__(self, document: QTextDocument, rules: LanguageRules) -> None:
        """
        :param document: 要上色的文件 / the document to highlight
        :param rules: 該語言的規則 / that language's rules
        """
        super().__init__(document)
        self._rules = rules
        self._patterns: list[tuple[QRegularExpression, QTextCharFormat]] = []
        keyword_format = _format_for("syntax_keyword_color")
        for keyword in rules.keywords:
            self._patterns.append(
                (QRegularExpression(rf"\b{re.escape(keyword)}\b"), keyword_format))
        number_format = _format_for("syntax_number_color")
        self._patterns.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), number_format))
        string_format = _format_for("syntax_string_color")
        for quote in rules.string_delimiters:
            escaped = re.escape(quote)
            self._patterns.append(
                (QRegularExpression(rf"{escaped}[^{escaped}\\]*(\\.[^{escaped}\\]*)*{escaped}"),
                 string_format))
        self._comment_format = _format_for("syntax_comment_color")

    def highlightBlock(self, text: str) -> None:
        """為一行上色 / Colour one line."""
        for pattern, text_format in self._patterns:
            matches = pattern.globalMatch(text)
            while matches.hasNext():
                match = matches.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), text_format)
        self._highlight_line_comment(text)
        self._highlight_block_comment(text)

    def _highlight_line_comment(self, text: str) -> None:
        """單行註解從標記處一路到行尾 / A line comment runs from its marker to the line end."""
        marker = self._rules.line_comment
        if not marker:
            return
        start = text.find(marker)
        if start >= 0:
            self.setFormat(start, len(text) - start, self._comment_format)

    def _highlight_block_comment(self, text: str) -> None:
        """
        區塊註解可能跨行，因此用區塊狀態記住是否還在註解裡
        A block comment may span lines, so the block state remembers whether one
        is still open.
        """
        if self._rules.block_comment is None:
            return
        opening, closing = self._rules.block_comment
        start = 0 if self.previousBlockState() == _INSIDE_BLOCK_COMMENT else text.find(opening)
        while start >= 0:
            end = text.find(closing, start + len(opening))
            if end < 0:
                self.setFormat(start, len(text) - start, self._comment_format)
                self.setCurrentBlockState(_INSIDE_BLOCK_COMMENT)
                return
            length = end - start + len(closing)
            self.setFormat(start, length, self._comment_format)
            start = text.find(opening, start + length)
        self.setCurrentBlockState(0)


def highlighter_for(document: QTextDocument, suffix: str) -> GenericHighlighter | None:
    """
    為某個副檔名建立高亮器
    Build a highlighter for a file suffix.

    :param document: 要上色的文件 / the document to highlight
    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: 高亮器，沒有對應規則時為 ``None`` / the highlighter, or ``None``
    """
    rules = rules_for(suffix)
    return GenericHighlighter(document, rules) if rules is not None else None

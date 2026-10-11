"""
把語法引擎的分類畫到文件上的高亮器
The highlighter that paints a syntax engine's categories onto a document.

這個高亮器不知道語法樹是什麼：它只把文件的文字交給 session，再問「第幾行有哪幾段、
各是什麼分類」，然後依主題上色。換一個解析器不必動這裡。
This highlighter does not know what a syntax tree is. It hands the document's
text to a session, asks which stretches of which line are what, and colours them
from the theme. Swapping the parser changes nothing here.

Qt 的高亮器只會重畫被編輯的那幾行，但語法上的影響可以遠得多：打開一個三引號，
後面每一行都變成字串。session 會回報語法因為這次編輯而不同的那幾行；編輯位置之後
的行，靠改變區塊狀態讓 Qt 在同一輪裡接著畫下去，之前的行則在事件迴圈的下一輪補畫。
Qt's highlighter repaints only the lines that were edited, yet the effect on the
syntax can reach much further: open a triple quote and every line after it turns
into a string. The session reports the lines whose syntax came out different.
Those after the edit are reached by changing the block state, which makes Qt
carry on within the same pass; those before it are repainted on the next turn of
the event loop.
"""
from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QTextDocument

from je_editor.core.syntax.syntax_model import LineSpan, SyntaxCategory, SyntaxSession
from je_editor.pyside_ui.code.syntax.highlight_rules import (
    HighlightRule, apply_rules, make_format, release_document
)

# 每一種分類用哪個主題顏色；沒列出的分類用預設的文字顏色
# The theme colour each category uses; a category not listed takes the default text colour
CATEGORY_COLOURS: dict[SyntaxCategory, str] = {
    SyntaxCategory.COMMENT: "syntax_comment_color",
    SyntaxCategory.STRING: "syntax_string_color",
    SyntaxCategory.ESCAPE: "syntax_builtin_color",
    SyntaxCategory.NUMBER: "syntax_number_color",
    SyntaxCategory.KEYWORD: "syntax_keyword_color",
    SyntaxCategory.LITERAL: "syntax_keyword_color",
    SyntaxCategory.KEY: "syntax_keyword_color",
    SyntaxCategory.FUNCTION: "syntax_function_color",
    SyntaxCategory.BUILTIN: "syntax_builtin_color",
    SyntaxCategory.TYPE: "syntax_builtin_color",
    SyntaxCategory.SPECIAL_VARIABLE: "syntax_self_color",
}
# Qt 把段落之間記成這個字元；語法引擎要的是換行
# Qt stores this character between paragraphs; the syntax engine wants a newline
_PARAGRAPH_SEPARATOR = " "
# 區塊狀態只用來告訴 Qt「下一行也要重畫」，在這兩個值之間來回切換
# The block state only tells Qt that the next line needs repainting too, by
# switching between these two values
_STATE_A = 0
_STATE_B = 1
# 編輯位置之前要補畫的行超過這個數目時，整份文件一次重畫；一行一行畫每行都會送出
# 一次「文字變了」的訊號
# When more lines than this need repainting before the edit, the whole document is
# repainted at once: line by line, every one of them sends a text-changed signal
SINGLE_REPAINT_LIMIT = 50


def category_formats() -> dict[SyntaxCategory, QTextCharFormat]:
    """
    依目前的主題為每一種分類建立格式
    Build the format of every category from the current theme.

    沒有顏色的分類也有一個（空的）格式：字串裡的插值要靠它把字串的顏色蓋回預設。
    A category without a colour gets a format too, an empty one: that is what
    puts an interpolation inside a string back to the default colour.

    :return: 每一種分類的格式 / the format of each category
    """
    return {category: make_format(CATEGORY_COLOURS.get(category, ""))
            for category in SyntaxCategory}


class TreeSitterHighlighter(QSyntaxHighlighter):
    """
    依語法引擎的分類上色的高亮器
    The highlighter that colours by a syntax engine's categories.
    """

    def __init__(self, document: QTextDocument, session: SyntaxSession,
                 extra_rules: Sequence[HighlightRule] = ()) -> None:
        """
        :param document: 要上色的文件 / the document to highlight
        :param session: 這份文件的語法分析 / the syntax analysis of this document
        :param extra_rules: 疊在語法分類之上的規則，例如插件登記的關鍵字
            rules laid over the categories, such as keywords a plugin registered
        """
        # 先不給文件：Qt 依連接的順序呼叫 slot，這個高亮器更新語法分析的 slot 要排在
        # Qt 自己重畫編輯行的 slot 之前，重畫時問到的才是新的語法樹。
        # No document yet: Qt calls slots in the order they were connected, and
        # this highlighter's slot that updates the analysis has to come before
        # Qt's own slot that repaints the edited lines, so the repaint asks an
        # up-to-date tree.
        super().__init__(None)
        self.setParent(document)
        self._session = session
        self._extra_rules = list(extra_rules)
        self._formats = category_formats()
        self._document: QTextDocument | None = document
        self._line_count = document.blockCount()
        # Qt 這一輪要一路畫到第幾行 / The line Qt's current pass has to carry on to
        self._carry_on_to = 0
        # 編輯位置之前、等著補畫的行 / The lines before the edit that wait to be repainted
        self._earlier: LineSpan | None = None
        self._catch_up = QTimer(self)
        self._catch_up.setSingleShot(True)
        self._catch_up.setInterval(0)
        self._catch_up.timeout.connect(self._repaint_earlier)
        document.contentsChange.connect(self._analyse_again)
        self._session.update(self._document_text())
        self.setDocument(document)

    @property
    def session(self) -> SyntaxSession:
        """這份文件的語法分析 / The syntax analysis of this document."""
        return self._session

    def detach(self) -> None:
        """
        停止上色並放開文件
        Stop highlighting and let go of the document.

        換成另一個高亮器之前要呼叫；不然舊的那一個仍然連在文件上繼續做白工。
        Called before another highlighter takes over: otherwise the old one stays
        connected to the document and keeps working for nothing.
        """
        self._catch_up.stop()
        self._earlier = None
        if self._document is not None:
            self._document.contentsChange.disconnect(self._analyse_again)
            self._document = None
        release_document(self)

    def highlightBlock(self, text: str) -> None:
        """為一行上色 / Colour one line."""
        line = self.currentBlock().blockNumber() + 1
        for span in self._session.spans(line):
            self.setFormat(span.column - 1, span.length, self._formats[span.category])
        apply_rules(self, text, self._extra_rules)
        if line < self._carry_on_to:
            # 狀態跟原本不同，Qt 就會接著畫下一行
            # A state that differs from before makes Qt go on to the next line
            self.setCurrentBlockState(
                _STATE_B if self.currentBlockState() != _STATE_B else _STATE_A)
        else:
            self._carry_on_to = 0

    def _document_text(self) -> str:
        """文件的文字，一個段落一行 / The document's text, one line per paragraph."""
        if self._document is None:
            return ""
        return self._document.toRawText().replace(_PARAGRAPH_SEPARATOR, "\n")

    def _analyse_again(self, position: int, _removed: int, _added: int) -> None:
        """
        文件變了：更新語法分析，並記下這次編輯之外還有哪些行要重畫
        The document changed: update the analysis, and note which lines beyond
        the edit itself have to be repainted.

        :param position: 編輯開始的位置 / where the edit starts
        """
        if self._document is None:
            return
        changed = self._session.update(self._document_text())
        if changed is None:
            return
        line_count = self._document.blockCount()
        shift, self._line_count = line_count - self._line_count, line_count
        self._carry_on_to = changed.last
        edited_line = self._document.findBlock(position).blockNumber() + 1
        if changed.first < edited_line:
            before = LineSpan(changed.first, edited_line - 1)
            self._earlier = _merged(self._earlier, before, shift, line_count)
            self._catch_up.start()

    def _repaint_earlier(self) -> None:
        """補畫編輯位置之前、語法也跟著變了的行 / Repaint the lines before the edit whose syntax changed too."""
        span, self._earlier = self._earlier, None
        if span is None or self._document is None:
            return
        if span.last - span.first >= SINGLE_REPAINT_LIMIT:
            self.rehighlight()
            return
        for line in range(span.first, span.last + 1):
            block = self._document.findBlockByNumber(line - 1)
            if block.isValid():
                self.rehighlightBlock(block)


def _merged(waiting: LineSpan | None, changed: LineSpan, shift: int, line_count: int) -> LineSpan:
    """
    把新回報的行併進還沒畫完的行
    Merge newly reported lines into the ones still waiting.

    還在等的行可能因為這次編輯多了或少了幾行而移位，所以往移動的方向放寬。多畫幾行
    沒有壞處，少畫才會留下舊的顏色。
    The waiting lines may have moved because this edit added or removed lines, so
    the span is widened in the direction they moved. Repainting a few lines too
    many is harmless; too few would leave stale colours behind.

    :param waiting: 還沒畫完的行 / the lines still waiting
    :param changed: 這次分析回報的行 / the lines this analysis reported
    :param shift: 這次編輯讓行數增加了多少，減少時為負
        how many lines this edit added, negative when it removed some
    :param line_count: 文件現在的行數 / how many lines the document has now
    :return: 要重畫的行 / the lines to repaint
    """
    if waiting is None:
        return changed
    first = min(changed.first, waiting.first + min(shift, 0))
    last = max(changed.last, waiting.last + max(shift, 0))
    return LineSpan(max(first, 1), min(last, line_count))

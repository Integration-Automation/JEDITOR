"""
同一份文件的第二個檢視
A second view of the same document.

分割檢視共用 ``QTextDocument``：兩邊看到的是同一份內容，任一邊編輯另一邊立刻
跟著變，捲動與游標則各自獨立，因此可以一邊看檔案開頭一邊改結尾。
A split view shares the ``QTextDocument``: both sides show one piece of content
and an edit in either appears in the other at once, while scrolling and the
caret stay independent — so the top of a file can be read while its end is
edited.

語法高亮是掛在文件上而不是編輯器上，因此第二個檢視不需要自己的高亮器就會上色。
Syntax highlighting attaches to the document rather than to an editor, so the
second view is highlighted without needing a highlighter of its own.
"""
from __future__ import annotations

from PySide6.QtGui import QFontMetricsF
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class SplitEditorView(QPlainTextEdit):
    """
    共用文件的輕量編輯檢視
    A lightweight editing view onto a shared document.
    """

    def __init__(self, source_editor: QPlainTextEdit, parent: QWidget | None = None) -> None:
        """
        :param source_editor: 要共用文件的主編輯器 / the editor whose document is shared
        :param parent: Qt 父元件 / the Qt parent
        """
        super().__init__(parent)
        self.setDocument(source_editor.document())
        self.setFont(source_editor.font())
        self.setLineWrapMode(source_editor.lineWrapMode())
        self.setTabStopDistance(
            QFontMetricsF(source_editor.font()).horizontalAdvance(" " * 8))
        # 從主編輯器目前的位置開始看，而不是從檔案開頭
        # Start where the main editor is, rather than at the top of the file
        self.setTextCursor(source_editor.textCursor())

    def closeEvent(self, event) -> None:
        """
        關閉前先放開共用文件
        Release the shared document before closing.

        若仍持有主編輯器的文件就被銷毀，Qt 會連帶清掉那份文件的檢視狀態；改指向
        一份空文件可以乾淨地脫鉤。
        Destroying this view while it still holds the main editor's document lets
        Qt tear down view state that document still needs; pointing it at an
        empty document detaches cleanly first.
        """
        self.setDocument(None)
        super().closeEvent(event)

from typing import Union

from PySide6 import QtGui
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QTextCharFormat, QTextFormat, QKeyEvent, QAction, QTextDocument, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter

from je_editor.pyside_ui.code.complete_list.total_complete_list import complete_list
from je_editor.pyside_ui.dialog.search_ui.search_text_box import SearchBox
from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter


class CodeEditor(QPlainTextEdit):
    """
    Extend QPlainTextEdit,
    Add line, edit tab distance, add highlighter, add search text
    """

    def __init__(self):
        super().__init__()
        self.search_box = None
        self.line_number: LineNumber = LineNumber(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)
        self.textChanged.connect(self.highlight_current_line)
        self.setTabStopDistance(
            QtGui.QFontMetricsF(self.font()).horizontalAdvance(' ') * 4
        )
        self.highlighter = PythonHighlighter(self.document())
        self.highlight_current_line()
        self.setLineWrapMode(self.LineWrapMode.NoWrap)
        # Search Text
        self.search_action = QAction("Search")
        self.search_action.setShortcut("Ctrl+f")
        self.search_action.triggered.connect(
            self.start_search_dialog
        )
        self.addAction(self.search_action)
        # Complete
        self.completer: Union[None, QCompleter] = None
        self.complete_list = complete_list
        self.set_complete(self.complete_list)

    def set_complete(self, list_to_complete: list = complete_list) -> None:
        """
        Set complete and bind.
        :param list_to_complete: keyword list to complete.
        :return: None
        """
        completer = QCompleter(list_to_complete)
        completer.activated.connect(self.insert_completion)
        completer.setWidget(self)
        completer.setWrapAround(False)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer = completer

    def insert_completion(self, completion) -> None:
        """
        insert complete keyword to editor.
        :param completion: completion text
        :return: None
        """
        if self.completer.widget() != self:
            return
        text_cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        text_cursor.movePosition(QTextCursor.MoveOperation.Left)
        text_cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
        text_cursor.insertText(completion[-extra:])
        self.setTextCursor(text_cursor)

    @property
    def text_under_cursor(self):
        # Find text under cursor
        text_cursor = self.textCursor()
        text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return text_cursor.selectedText()

    def focusInEvent(self, e) -> None:
        if self.completer:
            self.completer.setWidget(self)
        QPlainTextEdit.focusInEvent(self, e)

    def complete(self) -> None:
        """
        Keyword autocomplete
        :return:  None
        """
        prefix = self.text_under_cursor
        self.completer.setCompletionPrefix(prefix)
        popup = self.completer.popup()
        cursor_rect = self.cursorRect()
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        cursor_rect.setWidth(self.completer.popup().rect().size().width())
        self.completer.complete(cursor_rect)

    def start_search_dialog(self) -> None:
        """
        Show search box ui and bind.
        :return: None
        """
        # Search box connect to function
        self.search_box = SearchBox()
        self.search_box.search_back_button.clicked.connect(
            self.find_back_text
        )
        self.search_box.search_next_button.clicked.connect(
            self.find_next_text
        )
        self.search_box.show()

    def find_next_text(self) -> None:
        """
        Find next match text.
        :return: None
        """
        if self.search_box.isVisible():
            text = self.search_box.search_input.text()
            self.find(text)

    def find_back_text(self) -> None:
        """
        Find back match text.
        :return: None
        """
        if self.search_box.isVisible():
            text = self.search_box.search_input.text()
            self.find(text, QTextDocument.FindFlag.FindBackward)

    def line_number_paint(self, event) -> None:
        painter = QPainter(self.line_number)
        painter.fillRect(event.rect(), QColor(51, 51, 77))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(179, 179, 204))
                painter.drawText(
                    0,
                    top,
                    self.line_number.width(),
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignCenter,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def line_number_width(self) -> int:
        digits = len(str(self.blockCount()))
        space = 10 * digits
        return space

    def update_line_number_area_width(self, value) -> None:
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def resizeEvent(self, event) -> None:
        """
        Resize line number paint.
        :param event: QT event.
        :return: None
        """
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.line_number.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()),
        )

    def update_line_number_area(self, rect, dy) -> None:
        """
        Set line number.
        :param rect: line number rect.
        :param dy: update or not.
        :return: None
        """
        if dy:
            self.line_number.scroll(0, dy)
        else:
            self.line_number.update(
                0,
                rect.y(),
                self.line_number.width(),
                rect.height(),
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def highlight_current_line(self) -> None:
        """
        Change current line color.
        :return: None
        """
        selections = []
        if not self.isReadOnly():
            formats = QTextCharFormat()
            selection = QTextEdit.ExtraSelection()
            selection.format = formats
            color_of_the_line = QColor(92, 92, 138)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
            selection.format.setBackground(color_of_the_line)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections(selections)

    def keyPressEvent(self, event) -> None:
        """
        Catch Soft new line (key, shift + enter)
        :param event: keypress event
        :return: None
        """
        skip_popup_behavior_list = [
            Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Space
        ]
        need_complete_list = [
            Qt.Key.Key_A, Qt.Key.Key_B, Qt.Key.Key_C, Qt.Key.Key_D, Qt.Key.Key_E, Qt.Key.Key_F,
            Qt.Key.Key_G, Qt.Key.Key_H, Qt.Key.Key_I, Qt.Key.Key_J, Qt.Key.Key_K, Qt.Key.Key_L,
            Qt.Key.Key_M, Qt.Key.Key_N, Qt.Key.Key_O, Qt.Key.Key_P, Qt.Key.Key_Q, Qt.Key.Key_R,
            Qt.Key.Key_S, Qt.Key.Key_T, Qt.Key.Key_U, Qt.Key.Key_V, Qt.Key.Key_W, Qt.Key.Key_X,
            Qt.Key.Key_Y, Qt.Key.Key_Z, Qt.Key.Key_Backspace
        ]
        if self.completer.popup().isVisible() and event.key() in skip_popup_behavior_list:
            event.ignore()
            return
        key_event = QKeyEvent(event)
        if key_event.modifiers() and Qt.Modifier.SHIFT:
            key = key_event.key()
            if key == Qt.Key.Key_Enter or key == Qt.Key.Key_Return:
                event.ignore()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
        self.highlight_current_line()
        if event.key() in need_complete_list and self.completer is not None:
            self.complete()

    def mousePressEvent(self, event) -> None:
        # Highlight mouse click line
        super().mousePressEvent(event)
        self.highlight_current_line()


class LineNumber(QWidget):
    """
    Used to paint line number.
    """

    def __init__(self, editor):
        QWidget.__init__(self, parent=editor)
        self.editor = editor

    def paintEvent(self, event) -> None:
        self.editor.line_number_paint(event)

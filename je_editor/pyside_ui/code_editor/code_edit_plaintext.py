from PySide6 import QtGui
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QTextCharFormat, QTextFormat, QKeyEvent, QAction, QTextDocument
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit

from je_editor.pyside_ui.search_ui.search_text_box import SearchBox
from je_editor.pyside_ui.syntax.python_syntax import PythonHighlighter


class CodeEditor(QPlainTextEdit):
    """
    Extend QPlainTextEdit,
    Add line, edit tab distance, add highlighter, add search text
    """
    def __init__(self):
        super().__init__()
        self.line_number = LineNumber(self)
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

    def start_search_dialog(self) -> None:
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
        if self.search_box.isVisible():
            text = self.search_box.search_input.text()
            self.find(text)

    def find_back_text(self) -> None:
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
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.line_number.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()),
        )

    def update_line_number_area(self, rect, dy) -> None:
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

    def mousePressEvent(self, event) -> None:
        # Highlight mouse click line
        super().mousePressEvent(event)
        self.highlight_current_line()


class LineNumber(QWidget):

    def __init__(self, editor):
        QWidget.__init__(self, parent=editor)
        self.editor = editor

    def paintEvent(self, event) -> None:
        self.editor.line_number_paint(event)

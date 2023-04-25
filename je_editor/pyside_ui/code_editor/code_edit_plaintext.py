from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class CodeEditor(QPlainTextEdit):

    def __init__(self):
        super().__init__()
        self.line_number = LineNumber(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

    def line_number_paint(self, event):
        painter = QPainter(self.line_number)
        painter.fillRect(event.rect(), QColor(51, 51, 77))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(255, 255, 255))
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

    def line_number_width(self):
        digits = len(str(self.blockCount()))
        space = 10 * digits
        return space

    def update_line_number_area_width(self, value):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def resizeEvent(self, event):
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.line_number.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()),
        )

    def update_line_number_area(self, rect, dy):
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


class LineNumber(QWidget):

    def __init__(self, editor):
        QWidget.__init__(self, parent=editor)
        self.editor = editor

    def paintEvent(self, event):
        self.editor.line_number_paint(event)

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QPainter, QColor
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit


class LineNumberArea(QWidget):
    """
    Side widget for displaying line numbers.
    用來顯示行號的側邊元件。
    """

    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor  # 綁定主要的編輯器 / Bind to main editor

    def sizeHint(self):
        """
        Suggest width for line number area.
        建議行號區域的寬度。
        """
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """
        Delegate paint event to the main editor.
        將繪製事件交給主要編輯器處理。
        """
        self.code_editor.line_number_area_paint_event(event)


class LineNumberedCodeViewer(QPlainTextEdit):
    """
    QPlainTextEdit with line numbers.
    帶有行號顯示的文字編輯器。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        # === 信號連接 / Signal connections ===
        self.blockCountChanged.connect(self.update_line_number_area_width)  # 當行數改變時更新行號區寬度
        self.updateRequest.connect(self.update_line_number_area)  # 當需要重繪時更新行號區
        self.cursorPositionChanged.connect(self.highlight_current_line)  # 當游標移動時高亮當前行

        # 初始化行號區寬度與高亮
        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        """
        Calculate width of line number area based on digit count.
        根據行數位數計算行號區寬度。
        """
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """
        Adjust viewport margins to fit line number area.
        調整視口邊界以容納行號區。
        """
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """
        Update/redraw line number area when scrolling or editing.
        當滾動或編輯時更新行號區。
        """
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """
        Resize line number area when editor resizes.
        編輯器大小改變時調整行號區。
        """
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """
        Paint line numbers.
        繪製行號。
        """
        painter = QPainter(self.lineNumberArea)
        # 背景顏色依主題切換 / Background color depends on theme
        painter.fillRect(event.rect(), QColor(40, 40, 40) if getattr(self, "is_dark", False) else QColor(230, 230, 230))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                # 行號顏色依主題切換 / Line number color depends on theme
                painter.setPen(QColor("#d4d4d4") if getattr(self, "is_dark", False) else Qt.GlobalColor.black)
                painter.drawText(
                    0, top, self.lineNumberArea.width() - 2, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def highlight_current_line(self):
        """
        Highlight the current line where the cursor is.
        高亮顯示游標所在的行。
        """
        selection = QTextEdit.ExtraSelection()
        lineColor = QColor(50, 50, 50) if getattr(self, "is_dark", False) else QColor(232, 232, 255)
        selection.format.setBackground(lineColor)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()

        # Keep current-line extras for merging
        self._current_line_extras = [selection]

        # Merge with diff extras if present
        if hasattr(self, "_diff_extras"):
            merged = self._diff_extras + self._current_line_extras
        else:
            merged = self._current_line_extras

        self.setExtraSelections(merged)

    def apply_theme_to_editor(self, dark: bool):
        self.setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; }" if dark
                           else "QPlainTextEdit { background-color: white; color: black; }")
        # Re-trigger current line highlight with the new color
        self.highlight_current_line()

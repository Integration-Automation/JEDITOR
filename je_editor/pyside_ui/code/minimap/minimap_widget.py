"""
編輯器右側的縮圖
The minimap shown beside the editor.

把整份檔案畫成細長條的輪廓，並標出目前畫面的位置；點按或拖曳就能跳到該處。
Draws the whole file as thin bars showing the shape of the code, marks where the
screen currently is, and jumps there when clicked or dragged.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QPlainTextEdit, QWidget

from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.minimap.minimap_layout import (
    LINE_PIXELS,
    MINIMAP_WIDTH,
    bar_offset,
    bar_width,
    line_at_row,
    row_for_line,
    sample_step,
    viewport_band,
)

# 文件變更後多久重畫縮圖（毫秒）；輸入時不需要每個字都重畫
# How long after an edit the minimap repaints; it need not follow every keystroke
_REPAINT_DELAY_MS = 300


class MinimapWidget(QWidget):
    """
    顯示整份檔案輪廓的縮圖
    A minimap showing the shape of the whole file.
    """

    def __init__(self, code_edit: QPlainTextEdit, parent: QWidget | None = None) -> None:
        """
        :param code_edit: 要對應的編輯器 / the editor this minimap follows
        :param parent: Qt 父元件 / the Qt parent
        """
        super().__init__(parent)
        self._code_edit = code_edit
        self.setFixedWidth(MINIMAP_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._repaint_timer = QTimer(self)
        self._repaint_timer.setSingleShot(True)
        self._repaint_timer.setInterval(_REPAINT_DELAY_MS)
        self._repaint_timer.timeout.connect(self.update)

        code_edit.document().contentsChanged.connect(self._repaint_timer.start)
        code_edit.verticalScrollBar().valueChanged.connect(self.update)

    def _step(self) -> int:
        """目前的取樣間隔 / The sampling step in use right now."""
        return sample_step(self._code_edit.blockCount(), self.height())

    def _visible_line_count(self) -> int:
        """畫面上放得下幾行 / How many lines currently fit on screen."""
        line_height = max(1, self._code_edit.fontMetrics().height())
        return max(1, self._code_edit.viewport().height() // line_height)

    def paintEvent(self, event) -> None:
        """畫出每一行的輪廓與目前的可視範圍 / Draw each line's bar and the visible band."""
        painter = QPainter(self)
        painter.fillRect(event.rect(), actually_color_dict.get("minimap_background_color"))
        step = self._step()
        self._paint_bars(painter, step)
        self._paint_viewport_band(painter, step)
        painter.end()

    def _paint_bars(self, painter: QPainter, step: int) -> None:
        """把每一行畫成一條與其長度相當的長條 / Draw each line as a bar of its length."""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(actually_color_dict.get("minimap_line_color"))
        document = self._code_edit.document()
        line = 0
        while line < document.blockCount():
            block = document.findBlockByNumber(line)
            if not block.isValid():
                break
            row = row_for_line(line, step)
            if row > self.height():
                break
            width = bar_width(block.text(), MINIMAP_WIDTH)
            if width:
                painter.drawRect(bar_offset(block.text()), row, width, LINE_PIXELS - 1)
            line += step

    def _paint_viewport_band(self, painter: QPainter, step: int) -> None:
        """標出目前畫面對應的範圍 / Mark the part of the file currently on screen."""
        first_visible = self._code_edit.firstVisibleBlock().blockNumber()
        top, height = viewport_band(first_visible, self._visible_line_count(), step)
        painter.fillRect(
            0, top, self.width(), height, actually_color_dict.get("minimap_viewport_color"))

    def line_at_position(self, y_position: int) -> int:
        """
        取得縮圖上某個位置對應的行號
        The line a position in the minimap points at.

        :param y_position: 縮圖上的 y 座標 / the y coordinate in the minimap
        :return: 以 0 起算的行號 / the 0-based line number
        """
        return line_at_row(y_position, self._step(), self._code_edit.blockCount())

    def _scroll_to(self, y_position: int) -> None:
        """把編輯器捲到縮圖上被按下的位置 / Scroll the editor to the position clicked."""
        self._code_edit.jump_to_line(self.line_at_position(y_position) + 1)
        self.update()

    def mousePressEvent(self, event) -> None:
        """按下時跳到該處 / Jump to the position pressed."""
        self._scroll_to(int(event.position().y()))

    def mouseMoveEvent(self, event) -> None:
        """拖曳時持續跳轉 / Keep jumping while dragging."""
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._scroll_to(int(event.position().y()))

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QBrush, QTransform
from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsPathItem, QGraphicsSimpleTextItem,
)

from je_editor.git_client.commit_graph import CommitGraph
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# === 版面配置常數 / Layout constants ===
NODE_RADIUS = 6       # 節點半徑 / node radius
ROW_HEIGHT = 28       # 每一列高度 / row height
LANE_WIDTH = 22       # 每一條 lane 的寬度 / lane width
LEFT_MARGIN = 220     # 左側 SHA/訊息文字區域保留空間 / left margin for SHA/message text

# === 顏色設定 / Colors ===
EDGE_COLOR = QColor("#888")     # 邊線顏色 / edge color
TEXT_COLOR = QColor("#222")     # 文字顏色 / text color
BG_COLOR = QColor("#ffffff")    # 背景顏色 / background color

# Lane 顏色調色盤 / Lane color palette
LANE_COLORS = [
    QColor("#4C78A8"),
    QColor("#F58518"),
    QColor("#E45756"),
    QColor("#72B7B2"),
    QColor("#54A24B"),
    QColor("#EECA3B"),
    QColor("#B279A2"),
    QColor("#FF9DA6"),
    QColor("#9D755D"),
    QColor("#BAB0AC"),
]


def lane_color(lane: int) -> QColor:
    """
    根據 lane index 回傳顏色
    Return color based on lane index
    """
    if lane < 0:
        return QColor("#999")
    return LANE_COLORS[lane % len(LANE_COLORS)]


class CommitGraphView(QGraphicsView):
    """
    Git Commit Graph 視覺化檢視器
    Git commit graph visualization view
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_wrapper_get = language_wrapper.language_word_dict.get

        # 設定背景與抗鋸齒 / set background and antialiasing
        self.setBackgroundBrush(QBrush(BG_COLOR))
        self.setRenderHints(
            self.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
        )

        # 啟用拖曳與縮放模式 / enable drag and zoom mode
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # 建立場景 / create scene
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.graph: Optional[CommitGraph] = None
        self._padding = 40
        self._zoom = 1.0

    def set_graph(self, graph: CommitGraph):
        """
        設定 commit graph 並重新繪製
        Set commit graph and redraw
        """
        self.graph = graph
        self._redraw()

    def _lane_x(self, lane: int) -> float:
        # 計算 lane 的 X 座標 / calculate X position for lane
        return lane * LANE_WIDTH + NODE_RADIUS * 2

    def _row_y(self, row: int) -> float:
        # 計算 row 的 Y 座標 / calculate Y position for row
        return row * ROW_HEIGHT + NODE_RADIUS * 2

    def _redraw(self):
        """
        重新繪製整個 commit graph
        Redraw the entire commit graph
        """
        self._scene.clear()
        if not self.graph or not self.graph.nodes:
            self._scene.setSceneRect(QRectF(0, 0, 800, 400))
            return

        # === 繪製邊線 (父子關係) / Draw edges (parent-child relationships) ===
        edge_pen = QPen(EDGE_COLOR, 2)
        for row, node in enumerate(self.graph.nodes):
            if not node.parent_shas:
                continue
            x0 = self._lane_x(node.lane_index)
            y0 = self._row_y(row)
            for p in node.parent_shas:
                if p not in self.graph.index:
                    continue
                prow = self.graph.index[p]
                parent_node = self.graph.nodes[prow]
                x1 = self._lane_x(parent_node.lane_index)
                y1 = self._row_y(prow)

                # 使用三次貝茲曲線繪製邊線 / cubic Bezier curve for edge
                path = QPainterPath(QPointF(x0, y0))
                ctrl_y = (y0 + y1) / 2.0
                path.cubicTo(QPointF(x0, ctrl_y), QPointF(x1, ctrl_y), QPointF(x1, y1))
                edge_item = QGraphicsPathItem(path)
                edge_item.setPen(edge_pen)
                self._scene.addItem(edge_item)

        # === 繪製節點 (commit 圓點) / Draw nodes (commit circles) ===
        for row, node in enumerate(self.graph.nodes):
            cx = self._lane_x(node.lane_index)
            cy = self._row_y(row)

            circle = QGraphicsEllipseItem(
                QRectF(cx - NODE_RADIUS, cy - NODE_RADIUS, NODE_RADIUS * 2, NODE_RADIUS * 2)
            )
            circle.setBrush(QBrush(lane_color(node.lane_index)))
            circle.setPen(QPen(Qt.PenStyle.NoPen))
            # 設定 tooltip 顯示 commit 資訊 / tooltip with commit info
            circle.setToolTip(self.language_wrapper_get(
                "git_graph_tooltip_commit"
            ).format(short=node.commit_sha[:7],
                     author=node.author_name,
                     date=node.commit_date,
                     msg=node.commit_message))
            self._scene.addItem(circle)

            # 在左側顯示行號 / show row number on the left
            label_item = QGraphicsSimpleTextItem(str(row + 1))
            label_item.setBrush(QBrush(TEXT_COLOR))
            label_item.setPos(-30, cy - NODE_RADIUS * 2)
            self._scene.addItem(label_item)

        # 設定場景大小 / set scene rect
        self._scene.setSceneRect(
            QRectF(-40, 0,
                   self._lane_x(max(n.lane_index for n in self.graph.nodes) + 1) + self._padding,
                   self._row_y(len(self.graph.nodes)) + self._padding)
        )

    def _apply_initial_view(self):
        """
        初始縮放設定
        Apply initial zoom setting
        """
        self._zoom = 0.9
        self._apply_zoom_transform()

    # === 滑鼠滾輪縮放 / Mouse wheel zoom ===
    def wheelEvent(self, event):
        if not self._scene.items():
            return

        # Ctrl+滾輪縮放，否則正常滾動
        # Ctrl+Wheel to zoom, else scroll normally
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            factor = 1.0 + (0.1 if angle > 0 else -0.1)
            self._zoom = max(0.1, min(3.0, self._zoom * factor))
            self._apply_zoom_transform()
            event.accept()
        else:
            super().wheelEvent(event)

    def _apply_zoom_transform(self):
        """
        套用縮放轉換
        Apply zoom transform
        """
        t = QTransform()
        t.scale(self._zoom, self._zoom)
        self.setTransform(t)

    def resizeEvent(self, event):
        """
        視窗大小改變時的事件
        Handle resize event (keep scene rect, no auto-fit)
        """
        super().resizeEvent(event)
        # 保持場景大小，不自動縮放
        # Keep scene rect; do not auto-fit

    # === 外部控制輔助方法 / Helper for external controllers ===
    def focus_row(self, row: int):
        """
        將檢視器聚焦到指定的 row
        Center the view around a specific row
        """
        if not self.graph or row < 0 or row >= len(self.graph.nodes):
            return
        y = self._row_y(row)
        rect = QRectF(0, y - ROW_HEIGHT * 2, self._scene.width(), ROW_HEIGHT * 4)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        # 聚焦後恢復使用者縮放比例 / restore user zoom after focusing
        self._apply_zoom_transform()
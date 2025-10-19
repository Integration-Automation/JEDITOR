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

# Layout constants
NODE_RADIUS = 6
ROW_HEIGHT = 28
LANE_WIDTH = 22
LEFT_MARGIN = 220  # space for SHA/message text area on the left

# Colors
EDGE_COLOR = QColor("#888")
TEXT_COLOR = QColor("#222")
BG_COLOR = QColor("#ffffff")

# A small, repeatable lane palette
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
    if lane < 0:
        return QColor("#999")
    return LANE_COLORS[lane % len(LANE_COLORS)]


class CommitGraphView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_wrapper_get = language_wrapper.language_word_dict.get
        self.setBackgroundBrush(QBrush(BG_COLOR))
        self.setRenderHints(
            self.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.graph: Optional[CommitGraph] = None
        self._padding = 40
        self._zoom = 1.0

    def set_graph(self, graph: CommitGraph):
        self.graph = graph
        self._redraw()

    def _lane_x(self, lane: int) -> float:
        return lane * LANE_WIDTH + NODE_RADIUS * 2

    def _row_y(self, row: int) -> float:
        return row * ROW_HEIGHT + NODE_RADIUS * 2

    def _redraw(self):
        self._scene.clear()
        if not self.graph or not self.graph.nodes:
            self._scene.setSceneRect(QRectF(0, 0, 800, 400))
            return

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
                path = QPainterPath(QPointF(x0, y0))
                ctrl_y = (y0 + y1) / 2.0
                path.cubicTo(QPointF(x0, ctrl_y), QPointF(x1, ctrl_y), QPointF(x1, y1))
                edge_item = QGraphicsPathItem(path)
                edge_item.setPen(edge_pen)
                self._scene.addItem(edge_item)

        for row, node in enumerate(self.graph.nodes):
            cx = self._lane_x(node.lane_index)
            cy = self._row_y(row)

            circle = QGraphicsEllipseItem(
                QRectF(cx - NODE_RADIUS, cy - NODE_RADIUS, NODE_RADIUS * 2, NODE_RADIUS * 2)
            )
            circle.setBrush(QBrush(lane_color(node.lane_index)))
            circle.setPen(QPen(Qt.PenStyle.NoPen))
            circle.setToolTip(self.language_wrapper_get(
                "git_graph_tooltip_commit"
            ).format(short=node.commit_sha[:7],
                     author=node.author_name,
                     date=node.commit_date,
                     msg=node.commit_message))
            self._scene.addItem(circle)

            label_item = QGraphicsSimpleTextItem(str(row + 1))
            label_item.setBrush(QBrush(TEXT_COLOR))
            label_item.setPos(-30, cy - NODE_RADIUS * 2)
            self._scene.addItem(label_item)

        self._scene.setSceneRect(
            QRectF(-40, 0,
                   self._lane_x(max(n.lane_index for n in self.graph.nodes) + 1) + self._padding,
                   self._row_y(len(self.graph.nodes)) + self._padding)
        )

    def _apply_initial_view(self):
        # Start with a mild zoom to fit rows comfortably
        self._zoom = 0.9
        self._apply_zoom_transform()

    # Zoom and interaction
    def wheelEvent(self, event):
        if not self._scene.items():
            return

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
        t = QTransform()
        t.scale(self._zoom, self._zoom)
        self.setTransform(t)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep scene rect; do not auto-fit. Users control zoom.
        # Nothing else needed here.

    # Optional helpers for external controllers
    def focus_row(self, row: int):
        """
        Center the view around a specific row.
        """
        if not self.graph or row < 0 or row >= len(self.graph.nodes):
            return
        y = self._row_y(row)
        rect = QRectF(0, y - ROW_HEIGHT * 2, self._scene.width(), ROW_HEIGHT * 4)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        # Restore user zoom preference after focusing
        self._apply_zoom_transform()

from typing import Any

from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget, QHBoxLayout, QVBoxLayout, QLabel

from je_editor.pyside_ui.git_ui.code_diff_compare.line_number_code_viewer import LineNumberedCodeViewer


class SideBySideDiffWidget(QWidget):
    """
    Side-by-side diff viewer widget.
    左右對照的差異檢視元件。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # === 顏色設定 / Color configuration ===
        self.is_dark = True
        # 刪除行背景 / Deleted line background
        self.color_del = QColor("#ffcccc")  # 淡紅色，深淺背景都清楚
        # 新增行背景 / Added line background
        self.color_add = QColor("#ccffcc")  # 淡綠色，對比度佳
        # Hunk header 背景
        self.color_hunk = QColor("#cce5ff")  # 淡藍色，醒目但不刺眼
        # Diff header 背景
        self.color_header = QColor("#e0e0e0")  # 淺灰，適合標題區塊

        # === 左右檔名標籤 / File name labels ===
        self.leftLabel = QLabel("Left: (old)")
        self.rightLabel = QLabel("Right: (new)")
        font = QFont()
        font.setBold(True)
        self.leftLabel.setFont(font)
        self.rightLabel.setFont(font)

        # === 左右文字編輯器 / Left and right code editors ===
        self.leftEdit = LineNumberedCodeViewer()
        self.rightEdit = LineNumberedCodeViewer()
        for edit in (self.leftEdit, self.rightEdit):
            edit.setReadOnly(True)  # 設為唯讀 / Read-only
            edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # 不自動換行 / Disable line wrap
            mono = QFont("Consolas")  # 使用等寬字型 / Monospaced font
            mono.setStyleHint(QFont.StyleHint.Monospace)
            edit.setFont(mono)

        # === 版面配置 / Layout ===
        left_box = QVBoxLayout()
        left_box.addWidget(self.leftLabel)
        left_box.addWidget(self.leftEdit)

        right_box = QVBoxLayout()
        right_box.addWidget(self.rightLabel)
        right_box.addWidget(self.rightEdit)

        main = QHBoxLayout(self)
        left_container = QWidget(self)
        left_container.setLayout(left_box)
        right_container = QWidget(self)
        right_container.setLayout(right_box)
        main.addWidget(left_container)
        main.addWidget(right_container)

        # 同步左右捲軸 / Sync scrollbars
        self._sync_scrollbars()

        # 預設深色模式 / Default to dark theme
        self.set_dark_theme()

    def _sync_scrollbars(self) -> None:
        """
        Synchronize scrollbars between left and right editors.
        同步左右編輯器的捲軸。
        """
        self.leftEdit.verticalScrollBar().valueChanged.connect(
            self.rightEdit.verticalScrollBar().setValue
        )
        self.rightEdit.verticalScrollBar().valueChanged.connect(
            self.leftEdit.verticalScrollBar().setValue
        )
        self.leftEdit.horizontalScrollBar().valueChanged.connect(
            self.rightEdit.horizontalScrollBar().setValue
        )
        self.rightEdit.horizontalScrollBar().valueChanged.connect(
            self.leftEdit.horizontalScrollBar().setValue
        )

    def set_diff_text(self, diff_text: str) -> None:
        """
        Parse unified diff text and display it in side-by-side editors.
        解析 unified diff 文字並顯示在左右編輯器。
        """
        left_lines, right_lines, left_marks, right_marks, left_name, right_name = \
            self._parse_unified_diff(diff_text)

        self.leftLabel.setText(f"Left: {left_name or '(old)'}")
        self.rightLabel.setText(f"Right: {right_name or '(new)'}")

        self._set_text_with_highlights(self.leftEdit, left_lines, left_marks)
        self._set_text_with_highlights(self.rightEdit, right_lines, right_marks)

        # 游標移到開頭 / Move cursor to start
        self.leftEdit.moveCursor(QTextCursor.MoveOperation.Start)
        self.rightEdit.moveCursor(QTextCursor.MoveOperation.Start)

    def _set_text_with_highlights(self, edit: QPlainTextEdit, lines: list[str], marks: list[str]) -> None:
        """
        Set text and apply syntax highlighting based on diff marks.
        設定文字並依 diff 標記加上背景色。
        """
        edit.setPlainText("\n".join(lines))

        diff_extras = []
        for i, mark in enumerate(marks):
            fmt = QTextCharFormat()
            # Always set foreground so it won't fall back
            # 永遠設定前景色，避免 fallback
            fmt.setForeground(QColor("#d4d4d4") if self.is_dark else QColor("black"))

            if mark == "DEL":
                fmt.setBackground(self.color_del)
            elif mark == "ADD":
                fmt.setBackground(self.color_add)
            elif mark == "HUNK":
                fmt.setBackground(self.color_hunk)
            elif mark == "HDR":
                fmt.setBackground(self.color_header)
            else:
                continue

            sel = self._line_selection(edit, i, fmt)
            diff_extras.append(sel)

        # 保留 diff selections，方便主題切換時重用
        setattr(edit, "_diff_extras", diff_extras)

        # 嘗試合併其他高亮（例如 LineNumberedCodeViewer 的當前行高亮）
        if hasattr(edit, "_current_line_extras"):
            merged = diff_extras + edit._current_line_extras
        else:
            merged = diff_extras

        edit.setExtraSelections(merged)

    def _line_selection(self, edit: QPlainTextEdit, line_index: int, fmt: QTextCharFormat) -> QTextEdit.ExtraSelection:
        """
        Create a selection for a specific line with given format.
        建立某一行的選取區並套用格式。
        """
        sel = QTextEdit.ExtraSelection()
        sel.format = fmt
        cursor = edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_index):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        sel.cursor = cursor
        return sel

    @staticmethod
    def _classify_diff_line(raw: str) -> tuple[str, str | None, str, str | None]:
        """將單行 diff 分類成左右兩側的內容與標記 / Classify a diff line into left/right entries.

        Returns (left_text, left_mark, right_text, right_mark).
        """
        if raw.startswith("diff "):
            return raw, "HDR", raw, "HDR"
        if raw.startswith("--- "):
            return raw, "HDR", "", "HDR"
        if raw.startswith("+++ "):
            return "", "HDR", raw, "HDR"
        if raw.startswith("@@"):
            return raw, "HUNK", raw, "HUNK"
        if raw.startswith("-"):
            return raw, "DEL", "", None
        if raw.startswith("+"):
            return "", None, raw, "ADD"
        return raw, None, raw, None

    def _parse_unified_diff(self, diff_text: str) -> tuple:
        """將 unified diff 解析成左右行與標記 / Parse unified diff into paired lines and marks."""
        left_lines: list[str] = []
        right_lines: list[str] = []
        left_marks: list[str] = []
        right_marks: list[str] = []
        left_name, right_name = None, None

        def append_side(lines: list, marks: list, line: str, mark: str | None) -> None:
            lines.append(line)
            marks.append(mark or "CTX")

        def align() -> None:
            while len(left_lines) < len(right_lines):
                append_side(left_lines, left_marks, "", None)
            while len(right_lines) < len(left_lines):
                append_side(right_lines, right_marks, "", None)

        for raw in diff_text.splitlines():
            if raw.startswith("--- "):
                left_name = raw[4:].strip()
            elif raw.startswith("+++ "):
                right_name = raw[4:].strip()
            l_text, l_mark, r_text, r_mark = self._classify_diff_line(raw)
            append_side(left_lines, left_marks, l_text, l_mark)
            append_side(right_lines, right_marks, r_text, r_mark)
            align()

        return left_lines, right_lines, left_marks, right_marks, left_name, right_name

    def _background_for_line(self, text: str) -> QColor | None:
        """依行首字元選擇背景色 / Pick highlight background for a diff line."""
        if text.startswith("-"):
            return self.color_del
        if text.startswith("+"):
            return self.color_add
        if text.startswith("@@"):
            return self.color_hunk
        if text.startswith(("diff", "---", "+++")):
            return self.color_header
        return None

    def _rebuild_selection_format(self, sel: Any) -> Any:
        """根據主題重新計算單一 extra selection 的格式 / Rebuild a single selection format."""
        fmt: QTextCharFormat = QTextCharFormat(sel.format)
        fmt.setForeground(QColor("#d4d4d4") if self.is_dark else QColor("black"))
        cursor = sel.cursor
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        bg = self._background_for_line(cursor.selectedText())
        if bg is not None:
            fmt.setBackground(bg)
        sel.format = fmt
        return sel

    def _reapply_highlights_for_theme(self) -> None:
        """主題切換時重新套用高亮 / Reapply diff highlights when the theme changes."""
        for edit in (self.leftEdit, self.rightEdit):
            if not hasattr(edit, "_diff_extras"):
                continue
            updated = [self._rebuild_selection_format(sel) for sel in edit._diff_extras]
            edit._diff_extras = updated
            current_extras = getattr(edit, "_current_line_extras", [])
            edit.setExtraSelections(updated + current_extras)

    def set_dark_theme(self) -> None:
        """
        Apply dark theme colors.
        套用深色主題配色。
        """
        self.is_dark = True
        self.color_del = QColor(60, 20, 20)
        self.color_add = QColor(20, 60, 20)
        self.color_hunk = QColor(25, 25, 60)
        self.color_header = QColor(50, 50, 50)
        self.setStyleSheet("""QWidget { background-color: #1e1e1e; color: #d4d4d4; }""")
        self._reapply_highlights_for_theme()
        self.leftEdit.apply_theme_to_editor(dark=self.is_dark)
        self.rightEdit.apply_theme_to_editor(dark=self.is_dark)

    def set_light_theme(self) -> None:
        """
        Apply light  theme colors.
        套用淺色主題配色。
        """
        self.is_dark = False
        self.color_del = QColor(255, 230, 230)
        self.color_add = QColor(230, 255, 230)
        self.color_hunk = QColor(230, 230, 255)
        self.color_header = QColor(240, 240, 240)
        self.setStyleSheet("""QWidget { background-color: white; color: black; }""")
        self._reapply_highlights_for_theme()
        self.leftEdit.apply_theme_to_editor(dark=self.is_dark)
        self.rightEdit.apply_theme_to_editor(dark=self.is_dark)

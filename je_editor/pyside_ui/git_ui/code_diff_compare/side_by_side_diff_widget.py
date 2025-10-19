from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget, QHBoxLayout, QVBoxLayout, QLabel

from je_editor.pyside_ui.git_ui.code_diff_compare.line_number_code_viewer import LineNumberedCodeViewer


class SideBySideDiffWidget(QWidget):
    """
    Side-by-side diff viewer widget.
    左右對照的差異檢視元件。
    """

    def __init__(self, parent=None):
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
        leftBox = QVBoxLayout()
        leftBox.addWidget(self.leftLabel)
        leftBox.addWidget(self.leftEdit)

        rightBox = QVBoxLayout()
        rightBox.addWidget(self.rightLabel)
        rightBox.addWidget(self.rightEdit)

        main = QHBoxLayout(self)
        leftContainer = QWidget()
        leftContainer.setLayout(leftBox)
        rightContainer = QWidget()
        rightContainer.setLayout(rightBox)
        main.addWidget(leftContainer)
        main.addWidget(rightContainer)

        # 同步左右捲軸 / Sync scrollbars
        self._sync_scrollbars()

        # 預設深色模式 / Default to dark theme
        self.set_dark_theme()

    def _sync_scrollbars(self):
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

    def set_diff_text(self, diff_text: str):
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

    def _set_text_with_highlights(self, edit: QPlainTextEdit, lines, marks):
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

    def _line_selection(self, edit: QPlainTextEdit, line_index: int, fmt: QTextCharFormat):
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

    def _parse_unified_diff(self, diff_text: str):
        """
        Parse unified diff into left/right lines and marks.
        將 unified diff 解析成左右行與標記。
        """
        left_lines, right_lines, left_marks, right_marks = [], [], [], []
        left_name, right_name = None, None

        def add_left(line, mark=None):
            left_lines.append(line)
            left_marks.append(mark or "CTX")

        def add_right(line, mark=None):
            right_lines.append(line)
            right_marks.append(mark or "CTX")

        def align():
            # 對齊左右行數 / Align left and right line counts
            if len(left_lines) < len(right_lines):
                for _ in range(len(right_lines) - len(left_lines)):
                    add_left("")
            elif len(right_lines) < len(left_lines):
                for _ in range(len(left_lines) - len(right_lines)):
                    add_right("")

        for raw in diff_text.splitlines():
            if raw.startswith("diff "):
                add_left(raw, "HDR"); add_right(raw, "HDR"); align()
            elif raw.startswith("--- "):
                left_name = raw[4:].strip()
                add_left(raw, "HDR"); add_right("", "HDR"); align()
            elif raw.startswith("+++ "):
                right_name = raw[4:].strip()
                add_left("", "HDR"); add_right(raw, "HDR"); align()
            elif raw.startswith("@@"):
                add_left(raw, "HUNK"); add_right(raw, "HUNK"); align()
            elif raw.startswith("-"):
                add_left(raw, "DEL"); add_right("", None); align()
            elif raw.startswith("+"):
                add_left("", None); add_right(raw, "ADD"); align()
            else:
                add_left(raw, None); add_right(raw, None); align()

        return left_lines, right_lines, left_marks, right_marks, left_name, right_name

    def _reapply_highlights_for_theme(self):
        """
        Reapply highlights when theme changes.
        主題切換時重新套用高亮。
        """
        for edit in (self.leftEdit, self.rightEdit):
            if hasattr(edit, "_diff_extras"):
                updated = []
                for sel in edit._diff_extras:
                    fmt: QTextCharFormat = QTextCharFormat(sel.format)

                    # 前景色依主題切換
                    fmt.setForeground(QColor("#d4d4d4") if self.is_dark else QColor("black"))

                    # 依照 mark 更新背景色
                    cursor = sel.cursor
                    cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                    text = cursor.selectedText()

                    if text.startswith("-"):
                        fmt.setBackground(self.color_del)
                    elif text.startswith("+"):
                        fmt.setBackground(self.color_add)
                    elif text.startswith("@@"):
                        fmt.setBackground(self.color_hunk)
                    elif text.startswith("diff") or text.startswith("---") or text.startswith("+++"):
                        fmt.setBackground(self.color_header)

                    sel.format = fmt
                    updated.append(sel)

                edit._diff_extras = updated

                if hasattr(edit, "_current_line_extras"):
                    merged = updated + edit._current_line_extras
                else:
                    merged = updated
                edit.setExtraSelections(merged)

    def set_dark_theme(self):
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

    def set_light_theme(self):
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


from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union, List

import jedi  # Python 自動補全與靜態分析工具
from PySide6 import QtGui
from PySide6.QtCore import Qt, QRect, QTimer, QThread, Signal, QObject
from PySide6.QtGui import (
    QPainter, QTextCharFormat, QTextFormat, QKeyEvent, QAction,
    QTextDocument, QTextCursor, QTextOption, QColor, QWheelEvent
)
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QInputDialog

from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
from je_editor.pyside_ui.dialog.search_ui.search_text_box import SearchBox
from je_editor.pyside_ui.dialog.search_ui.search_replace_widget import SearchReplaceDialog
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入，避免循環引用
# Only imported for type checking, avoids circular imports
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    from je_editor.pyside_ui.main_ui.editor.editor_widget_dock import FullEditorWidget


class _JediCompleteWorker(QObject):
    """背景執行 Jedi 自動補全 / Run Jedi autocomplete in background thread"""
    finished = Signal(list)  # list of completion names

    def __init__(self, code: str, line: int, column: int, env: jedi.api.environment.Environment | None = None) -> None:
        super().__init__()
        self._code = code
        self._line = line
        self._column = column
        self._env = env

    def run(self) -> None:
        try:
            if self._env is not None:
                script = jedi.Script(code=self._code, environment=self._env)
            else:
                script = jedi.Script(code=self._code)
            completions = script.complete(self._line, self._column)
            names = [c.name for c in completions]
            self.finished.emit(names)
        except Exception:
            self.finished.emit([])


def venv_check() -> Path:
    """檢查當前工作目錄下是否有 venv 資料夾 / Check if venv exists in current working directory"""
    jeditor_logger.info("code_edit_plaintext.py venv check")
    venv_path = Path.cwd() / "venv"
    return venv_path


class CodeEditor(QPlainTextEdit):
    """
    自訂的程式碼編輯器，繼承 QPlainTextEdit
    Custom code editor extending QPlainTextEdit

    功能：
    - 行號顯示 (Line number area)
    - Tab 縮排距離設定
    - Python 語法高亮 (Syntax highlighting)
    - 搜尋功能 (Search box)
    - 自動補全 (Autocomplete with Jedi)
    """

    def __init__(self, main_window: Union[EditorWidget, FullEditorWidget]) -> None:
        jeditor_logger.info(f"Init CodeEditor main_window: {main_window}")
        super().__init__()

        # Jedi 環境，用於 Python 自動補全
        self.env = None
        self.check_env()

        # 主視窗 (父元件)
        self.main_window = main_window
        self.current_file = main_window.current_file

        # 定義哪些按鍵不會觸發補全視窗
        self.skip_popup_behavior_list = [
            Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Up, Qt.Key.Key_Down,
            Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Space, Qt.Key.Key_Backspace
        ]

        # 定義哪些按鍵會觸發補全 (A-Z)
        self.need_complete_list = [
            Qt.Key.Key_A, Qt.Key.Key_B, Qt.Key.Key_C, Qt.Key.Key_D, Qt.Key.Key_E, Qt.Key.Key_F,
            Qt.Key.Key_G, Qt.Key.Key_H, Qt.Key.Key_I, Qt.Key.Key_J, Qt.Key.Key_K, Qt.Key.Key_L,
            Qt.Key.Key_M, Qt.Key.Key_N, Qt.Key.Key_O, Qt.Key.Key_P, Qt.Key.Key_Q, Qt.Key.Key_R,
            Qt.Key.Key_S, Qt.Key.Key_T, Qt.Key.Key_U, Qt.Key.Key_V, Qt.Key.Key_W, Qt.Key.Key_X,
            Qt.Key.Key_Y, Qt.Key.Key_Z
        ]

        # 搜尋框 (延遲建立)
        self.search_box = None

        # 行號區域 (LineNumber 是另一個自訂類別)
        self.line_number: LineNumber = LineNumber(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        # 當文字改變時，重新高亮當前行
        self.textChanged.connect(self.highlight_current_line)

        # 設定 Tab 寬度 (以字元寬度計算)
        self.setTabStopDistance(
            QtGui.QFontMetricsF(self.font()).horizontalAdvance("        ")
        )

        # Python 語法高亮
        self.highlighter = PythonHighlighter(self.document(), main_window=self)
        self.highlight_current_line()

        # 關閉自動換行，改為單行顯示
        self.setLineWrapMode(self.LineWrapMode.NoWrap)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)

        # 搜尋功能 (Ctrl+F)
        self.search_action = QAction("Search")
        self.search_action.setShortcut("Ctrl+f")
        self.search_action.triggered.connect(self.start_search_dialog)
        self.addAction(self.search_action)

        # 搜尋與取代 (Ctrl+Shift+F) / Search & Replace shortcut
        self.search_replace_action = QAction("Search & Replace")
        self.search_replace_action.setShortcut("Ctrl+Shift+f")
        self.search_replace_action.triggered.connect(self.open_search_replace_dialog)
        self.addAction(self.search_replace_action)

        # 跳到指定行 (Ctrl+G) / Go to Line shortcut
        self.goto_line_action = QAction("Go to Line")
        self.goto_line_action.setShortcut("Ctrl+g")
        self.goto_line_action.triggered.connect(self.go_to_line)
        self.addAction(self.goto_line_action)

        # 自動補全初始化
        self.completer: Union[None, QCompleter] = None
        self.set_complete([])

        # 自動補全 debounce 計時器 (300ms) / Autocomplete debounce timer
        self._complete_timer = QTimer(self)
        self._complete_timer.setSingleShot(True)
        self._complete_timer.setInterval(300)
        self._complete_timer.timeout.connect(self.complete)

        # 背景補全執行緒與 worker / Background completion thread and worker
        self._complete_thread: Union[QThread, None] = None
        self._complete_worker: Union[_JediCompleteWorker, None] = None

        # 匹配括號高亮 / Matching bracket highlight
        self._bracket_pairs_chars = {'(': ')', ')': '(', '[': ']', ']': '[', '{': '}', '}': '{'}
        self._bracket_open = set('([{')
        self.cursorPositionChanged.connect(self._highlight_matching_bracket)

    def reset_highlighter(self) -> None:
        """重設語法高亮 / Reset syntax highlighter"""
        jeditor_logger.info("CodeEditor reset_highlighter")
        self.highlighter = PythonHighlighter(self.document(), main_window=self)
        self.highlight_current_line()

    def check_env(self) -> None:
        """檢查虛擬環境並建立 Jedi 環境 / Check venv and create Jedi environment"""
        jeditor_logger.info("CodeEditor check_env")
        path = venv_check()
        if path.exists():
            self.env = jedi.create_environment(str(path))

    def set_complete(self, list_to_complete: list) -> None:
        """
        設定自動補全清單
        Set completion list
        """
        jeditor_logger.info(f"CodeEditor set_complete list_to_complete: {list_to_complete}")
        completer = QCompleter(list_to_complete)
        completer.activated.connect(self.insert_completion)
        completer.setWidget(self)
        completer.setWrapAround(False)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer = completer

    def insert_completion(self, completion: str) -> None:
        """
        插入補全文字
        Insert completion text into editor
        """
        jeditor_logger.info(f"CodeEditor insert_completion completion: {completion}")
        if self.completer.widget() != self:
            return
        text_cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        text_cursor.movePosition(QTextCursor.MoveOperation.Left)
        text_cursor.movePosition(QTextCursor.MoveOperation.EndOfWord)
        text_cursor.insertText(completion[-extra:])
        self.setTextCursor(text_cursor)

    @property
    def text_under_cursor(self) -> str:
        """取得游標下的文字 / Get text under cursor"""
        text_cursor = self.textCursor()
        text_cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return text_cursor.selectedText()

    def focusInEvent(self, e: QtGui.QFocusEvent) -> None:
        """當編輯器獲得焦點時，確保 completer 綁定正確"""
        if self.completer:
            self.completer.setWidget(self)
        QPlainTextEdit.focusInEvent(self, e)

    def complete(self) -> None:
        """
        使用 Jedi 在背景執行緒進行自動補全，避免阻塞 UI
        Run Jedi autocomplete in background thread to avoid blocking UI
        """
        # 如果上一次補全還在執行，跳過 / Skip if previous completion is still running
        if self._complete_thread is not None and self._complete_thread.isRunning():
            return

        code = self.toPlainText()
        line = self.textCursor().blockNumber() + 1
        column = self.textCursor().positionInBlock()

        self._complete_thread = QThread(self)
        self._complete_worker = _JediCompleteWorker(code, line, column, self.env)
        self._complete_worker.moveToThread(self._complete_thread)
        self._complete_thread.started.connect(self._complete_worker.run)
        self._complete_worker.finished.connect(self._on_complete_results)
        self._complete_worker.finished.connect(self._complete_thread.quit)
        self._complete_thread.finished.connect(self._complete_thread.deleteLater)
        self._complete_thread.start()

    def _on_complete_results(self, names: list) -> None:
        """
        接收背景執行緒的補全結果並顯示
        Receive completion results from background thread and display
        """
        if names:
            self.set_complete(names)

        prefix = self.text_under_cursor
        self.completer.setCompletionPrefix(prefix)
        popup = self.completer.popup()
        cursor_rect = self.cursorRect()
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        cursor_rect.setWidth(self.completer.popup().rect().size().width())
        self.completer.complete(cursor_rect)

    def go_to_line(self) -> None:
        """跳到指定行數 / Go to a specific line number"""
        max_line = self.blockCount()
        line, ok = QInputDialog.getInt(
            self, "Go to Line", f"Line number (1-{max_line}):",
            value=self.textCursor().blockNumber() + 1,
            min=1, max=max_line
        )
        if ok:
            block = self.document().findBlockByNumber(line - 1)
            if block.isValid():
                cursor = self.textCursor()
                cursor.setPosition(block.position())
                self.setTextCursor(cursor)
                self.centerCursor()
                self.highlight_current_line()

    def open_search_replace_dialog(self) -> None:
        """開啟搜尋與取代對話框 / Open Search & Replace dialog"""
        jeditor_logger.info("CodeEditor open_search_replace_dialog")
        editor_widget = self.main_window
        dialog = SearchReplaceDialog(editor_widget, parent=self)
        # 如果有選取文字，自動帶入搜尋欄 / Pre-fill with selected text
        cursor = self.textCursor()
        if cursor.hasSelection():
            dialog.search_input.setText(cursor.selectedText())
        dialog.search_input.setFocus()
        dialog.show()

    def start_search_dialog(self) -> None:
        """顯示搜尋框 / Show search box"""
        jeditor_logger.info("CodeEditor start_search_dialog")
        self.search_box = SearchBox()
        self.search_box.search_back_button.clicked.connect(self.find_back_text)
        self.search_box.search_next_button.clicked.connect(
            self.find_next_text
        )
        self.search_box.show()

    def find_next_text(self) -> None:
        """
        找到下一個符合的文字
        Find next match text
        """
        jeditor_logger.info("CodeEditor find_next_text")
        if self.search_box.isVisible():
            text = self.search_box.search_input.text()
            self.find(text)

    def find_back_text(self) -> None:
        """
        找到上一個符合的文字
        Find previous match text
        """
        jeditor_logger.info("CodeEditor find_back_text")
        if self.search_box.isVisible():
            text = self.search_box.search_input.text()
            self.find(text, QTextDocument.FindFlag.FindBackward)

    def line_number_paint(self, event: QtGui.QPaintEvent) -> None:
        """
        繪製行號區域
        Paint line number area
        """
        painter = QPainter(self.line_number)
        # 填滿背景色
        painter.fillRect(event.rect(), actually_color_dict.get("line_number_background_color"))

        # 從第一個可見區塊開始
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # 逐行繪製行號
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(actually_color_dict.get("line_number_color"))
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
        """
        計算行號區域寬度
        Calculate line number area width
        """
        digits = len(str(self.blockCount()))  # 根據總行數決定位數
        space = 12 * digits
        return space

    def update_line_number_area_width(self, value: int) -> None:
        """
        更新行號區域寬度
        Update line number area width
        """
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """
        視窗大小改變時，調整行號區域
        Resize line number paint area
        """
        QPlainTextEdit.resizeEvent(self, event)
        cr = self.contentsRect()
        self.line_number.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_width(), cr.height()),
        )

    def update_line_number_area(self, rect: QRect, dy: int) -> None:
        """
        更新行號顯示
        Update line number area
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
        高亮目前所在行
        Highlight current line
        """
        selections = []
        if not self.isReadOnly():
            formats = QTextCharFormat()
            selection = QTextEdit.ExtraSelection()
            selection.format = formats
            color_of_the_line = actually_color_dict.get("current_line_color")
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            selections.append(selection)
            selection.format.setBackground(color_of_the_line)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections(selections)

    def _highlight_matching_bracket(self) -> None:
        """
        高亮匹配的括號
        Highlight matching bracket when cursor is on a bracket character
        """
        selections = []
        # 保留當前行高亮 / Keep current line highlight
        if not self.isReadOnly():
            fmt = QTextCharFormat()
            sel = QTextEdit.ExtraSelection()
            sel.format = fmt
            sel.format.setBackground(actually_color_dict.get("current_line_color"))
            sel.format.setProperty(QTextFormat.FullWidthSelection, True)
            sel.cursor = self.textCursor()
            sel.cursor.clearSelection()
            selections.append(sel)

        cursor = self.textCursor()
        doc = self.document()
        pos = cursor.position()
        text = doc.toPlainText()

        if pos < len(text) and text[pos] in self._bracket_pairs_chars:
            char = text[pos]
            match_pos = self._find_matching_bracket(text, pos, char)
            if match_pos is not None:
                bracket_fmt = QTextCharFormat()
                bracket_fmt.setBackground(QColor("#5a5a7a"))
                bracket_fmt.setForeground(QColor("#ffffff"))
                for p in (pos, match_pos):
                    sel = QTextEdit.ExtraSelection()
                    c = QTextCursor(doc)
                    c.setPosition(p)
                    c.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
                    sel.cursor = c
                    sel.format = bracket_fmt
                    selections.append(sel)

        self.setExtraSelections(selections)

    def _find_matching_bracket(self, text: str, pos: int, char: str) -> Union[int, None]:
        """
        找到匹配的括號位置
        Find position of matching bracket
        """
        match = self._bracket_pairs_chars[char]
        is_open = char in self._bracket_open
        direction = 1 if is_open else -1
        depth = 0
        i = pos
        while 0 <= i < len(text):
            if text[i] == char:
                depth += 1
            elif text[i] == match:
                depth -= 1
                if depth == 0:
                    return i
            i += direction
        return None

    def jump_to_matching_bracket(self) -> None:
        """
        跳到匹配的括號位置 (Ctrl+Shift+\\)
        Jump to matching bracket
        """
        cursor = self.textCursor()
        text = self.document().toPlainText()
        pos = cursor.position()
        if pos < len(text) and text[pos] in self._bracket_pairs_chars:
            match_pos = self._find_matching_bracket(text, pos, text[pos])
            if match_pos is not None:
                cursor.setPosition(match_pos)
                self.setTextCursor(cursor)
                self.centerCursor()

    def duplicate_line(self) -> None:
        """
        複製當前行 (Ctrl+D)
        Duplicate current line
        """
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertText("\n" + line_text)
        self.setTextCursor(cursor)

    def _toggle_comment_block_range(self, cursor: QTextCursor) -> tuple[int, int]:
        """取得要切換註解的 block 區間 / Get block range to toggle comment."""
        if cursor.hasSelection():
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            cursor.setPosition(start)
            start_block = cursor.blockNumber()
            cursor.setPosition(end)
            end_block = cursor.blockNumber()
        else:
            start_block = end_block = cursor.blockNumber()
        return start_block, end_block

    def _all_blocks_commented(self, cursor: QTextCursor, start_block: int, end_block: int) -> bool:
        """判斷範圍內所有行是否都以 # 開頭 / Check if every block starts with '#'."""
        cursor.setPosition(self.document().findBlockByNumber(start_block).position())
        for _ in range(end_block - start_block + 1):
            if not cursor.block().text().lstrip().startswith("#"):
                return False
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        return True

    def _uncomment_current_block(self, cursor: QTextCursor) -> None:
        """移除當前行的 # 與後續一個空格 / Remove '#' and following single space."""
        line = cursor.block().text()
        idx = line.index("#") if "#" in line else -1
        if idx < 0:
            return
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        for _ in range(idx):
            cursor.movePosition(QTextCursor.MoveOperation.Right)
        cursor.deleteChar()
        new_line = cursor.block().text()
        if len(new_line) > idx and new_line[idx] == " ":
            cursor.deleteChar()

    def toggle_comment(self) -> None:
        """切換註解 (Ctrl+/) / Toggle comment for current line or selected lines."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        start_block, end_block = self._toggle_comment_block_range(cursor)
        all_commented = self._all_blocks_commented(cursor, start_block, end_block)

        cursor.setPosition(self.document().findBlockByNumber(start_block).position())
        for _ in range(end_block - start_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            if all_commented:
                self._uncomment_current_block(cursor)
            else:
                cursor.insertText("# ")
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()

    def move_line(self, direction: int) -> None:
        """
        移動當前行 (Alt+Up/Down)
        Move current line up or down
        :param direction: -1 上移, 1 下移 / -1 up, 1 down
        """
        cursor = self.textCursor()
        block_num = cursor.blockNumber()
        target = block_num + direction

        if target < 0 or target >= self.document().blockCount():
            return

        cursor.beginEditBlock()
        # 選取當前行
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()
        cursor.removeSelectedText()

        if direction < 0:
            # 上移：刪除前面的換行，在上一行前插入
            cursor.deletePreviousChar()  # 刪除前面的 \n
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            cursor.insertText(line_text + "\n")
            cursor.movePosition(QTextCursor.MoveOperation.Up)
        else:
            # 下移：刪除後面的換行，在下一行後插入
            cursor.deleteChar()  # 刪除後面的 \n
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertText("\n" + line_text)

        cursor.endEditBlock()
        self.setTextCursor(cursor)
        self.highlight_current_line()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """
        滑鼠滾輪事件：Ctrl+滾輪縮放字型
        Mouse wheel: Ctrl+wheel to zoom font size
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            elif delta < 0:
                self._zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def _zoom_in(self) -> None:
        """放大字型 / Zoom in"""
        font = self.font()
        size = font.pointSize()
        if size < 72:
            font.setPointSize(size + 1)
            self.setFont(font)
            self.setTabStopDistance(
                QtGui.QFontMetricsF(font).horizontalAdvance("        ")
            )

    def _zoom_out(self) -> None:
        """縮小字型 / Zoom out"""
        font = self.font()
        size = font.pointSize()
        if size > 6:
            font.setPointSize(size - 1)
            self.setFont(font)
            self.setTabStopDistance(
                QtGui.QFontMetricsF(font).horizontalAdvance("        ")
            )

    # 自動關閉括號配對 / Auto-close bracket pairs
    _BRACKET_PAIRS = {
        Qt.Key.Key_ParenLeft: ("(", ")"),
        Qt.Key.Key_BracketLeft: ("[", "]"),
        Qt.Key.Key_BraceLeft: ("{", "}"),
        Qt.Key.Key_QuoteDbl: ('"', '"'),
        Qt.Key.Key_Apostrophe: ("'", "'"),
    }

    @staticmethod
    def _leading_space_count(text: str, limit: int = 4) -> int:
        """回傳開頭最多 limit 個的空白字元數 / Count leading spaces up to `limit`."""
        spaces = 0
        for ch in text:
            if ch == " " and spaces < limit:
                spaces += 1
            else:
                break
        return spaces

    def _unindent_current_block(self, cursor: QTextCursor) -> None:
        """移除當前行開頭最多 4 個空白 / Remove up to 4 leading spaces on the current line."""
        spaces = self._leading_space_count(cursor.block().text(), limit=4)
        if spaces == 0:
            return
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        for _ in range(spaces):
            cursor.deleteChar()

    def _indent_selection(self, indent: bool = True) -> None:
        """對選取的多行進行縮排或取消縮排 / Indent or unindent selected lines."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        start, end = cursor.selectionStart(), cursor.selectionEnd()

        cursor.setPosition(start)
        start_block = cursor.blockNumber()
        cursor.setPosition(end)
        end_block = cursor.blockNumber()

        cursor.setPosition(start)
        for _ in range(end_block - start_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            if indent:
                cursor.insertText("    ")
            else:
                self._unindent_current_block(cursor)
            cursor.movePosition(QTextCursor.MoveOperation.NextBlock)
        cursor.endEditBlock()

    def _handle_ctrl_shortcuts(self, event: QKeyEvent) -> bool:
        """處理 Ctrl 組合鍵 / Handle Ctrl shortcuts; return True if consumed."""
        key = event.key()
        modifiers = event.modifiers()
        if key == Qt.Key.Key_D:
            self.duplicate_line()
            return True
        if key == Qt.Key.Key_Slash:
            self.toggle_comment()
            return True
        if key == Qt.Key.Key_Backslash and modifiers & Qt.KeyboardModifier.ShiftModifier:
            self.jump_to_matching_bracket()
            return True
        if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self._zoom_in()
            return True
        if key == Qt.Key.Key_Minus:
            self._zoom_out()
            return True
        if key == Qt.Key.Key_B:
            self._jump_to_definition()
            return True
        return False

    def _handle_alt_shortcuts(self, event: QKeyEvent) -> bool:
        """處理 Alt 組合鍵 / Handle Alt shortcuts; return True if consumed."""
        key = event.key()
        if key == Qt.Key.Key_Up:
            self.move_line(-1)
            return True
        if key == Qt.Key.Key_Down:
            self.move_line(1)
            return True
        return False

    def _jump_to_definition(self) -> None:
        """使用 Jedi 跳轉到符號定義 / Use Jedi to jump to symbol definition."""
        if self.env is not None:
            script = jedi.Script(code=self.toPlainText(), environment=self.env)
        else:
            script = jedi.Script(code=self.toPlainText())
        goto_list: List[jedi.api.classes.Name] = script.goto(
            self.textCursor().blockNumber() + 1, self.textCursor().positionInBlock())
        if not goto_list:
            return
        path = goto_list[0].module_path
        if path is not None and path.exists():
            if self.main_window.current_file != str(path):
                self.main_window.main_window.go_to_new_tab(path)
            return
        target_line = goto_list[0].line - 1
        cursor = self.textCursor()
        block = self.document().findBlockByNumber(target_line)
        if block.isValid():
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)

    def _handle_tab_indent(self, event: QKeyEvent) -> bool:
        """處理 Tab/Shift+Tab 區塊縮排 / Handle block indent; return True if consumed."""
        key = event.key()
        if key == Qt.Key.Key_Tab and self.textCursor().hasSelection():
            self._indent_selection(indent=True)
            return True
        if key == Qt.Key.Key_Backtab:
            if self.textCursor().hasSelection():
                self._indent_selection(indent=False)
            return True
        return False

    def _handle_enter_autoindent(self, event: QKeyEvent) -> None:
        """Enter 自動縮排 / Auto-indent on Enter."""
        cursor = self.textCursor()
        line = cursor.block().text()
        indent = ""
        for ch in line:
            if ch in (" ", "\t"):
                indent += ch
            else:
                break
        if line.rstrip().endswith(":"):
            indent += "    "
        super().keyPressEvent(event)
        if indent:
            self.textCursor().insertText(indent)
        self.highlight_current_line()

    def _handle_bracket_autoclose(self, event: QKeyEvent) -> None:
        """自動關閉括號 / Auto-close brackets."""
        key = event.key()
        open_char, close_char = self._BRACKET_PAIRS[key]
        cursor = self.textCursor()
        if open_char == close_char:
            pos = cursor.positionInBlock()
            line = cursor.block().text()
            if pos > 0 and line[pos - 1] == open_char:
                super().keyPressEvent(event)
                self.highlight_current_line()
                return
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(open_char + selected + close_char)
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)
            cursor = self.textCursor()
            cursor.insertText(close_char)
            cursor.movePosition(QTextCursor.MoveOperation.Left)
            self.setTextCursor(cursor)
        self.highlight_current_line()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """鍵盤事件處理 / Handle key press events (dispatches to helpers)."""
        key = event.key()
        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ControlModifier and self._handle_ctrl_shortcuts(event):
            return

        if modifiers & Qt.KeyboardModifier.AltModifier and self._handle_alt_shortcuts(event):
            return

        if self._handle_tab_indent(event):
            return

        # 補全視窗開啟時，攔截不該觸發的按鍵 / Intercept keys that should close completion popup
        if self.completer.popup().isVisible() and key in self.skip_popup_behavior_list:
            self.completer.popup().close()
            event.ignore()
            return

        # Shift+Enter → 忽略 (避免軟換行影響行號)
        if modifiers & Qt.KeyboardModifier.ShiftModifier and key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            event.ignore()
            return

        if key in (Qt.Key.Key_Enter, Qt.Key.Key_Return) and not modifiers:
            self._handle_enter_autoindent(event)
            return

        if key in self._BRACKET_PAIRS and not modifiers & Qt.KeyboardModifier.ControlModifier:
            self._handle_bracket_autoclose(event)
            return

        super().keyPressEvent(event)
        self.highlight_current_line()

        if key in self.need_complete_list and self.completer is not None:
            if self.completer.popup().isVisible():
                self.completer.popup().close()
            self._complete_timer.start()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        滑鼠點擊事件
        Mouse press event
        """
        super().mousePressEvent(event)
        self.highlight_current_line()


class LineNumber(QWidget):
    """
    行號區域元件
    Widget used to paint line numbers
    """

    def __init__(self, editor: CodeEditor) -> None:
        jeditor_logger.info("Init LineNumber")
        QWidget.__init__(self, parent=editor)
        self.editor = editor

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        呼叫編輯器的 line_number_paint 來繪製行號
        Delegate painting to CodeEditor.line_number_paint
        """
        self.editor.line_number_paint(event)

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

from je_editor.pyside_ui.code.bookmark.bookmark_manager import BookmarkManager
from je_editor.pyside_ui.code.folding.folding_manager import FoldingManager
from je_editor.pyside_ui.code.selection.smart_selection_manager import SmartSelectionManager
from je_editor.utils.indentation.indent_convert import (
    convert_leading_spaces_to_tabs, convert_leading_tabs_to_spaces,
    detect_indent_width, detect_indentation_uses_tabs
)
from je_editor.utils.line_ops.line_operations import (
    join_lines, natural_sort, remove_blank_lines, reverse_lines, sort_lines, unique_lines
)
from je_editor.utils.navigation.location_history import LocationHistory
from je_editor.utils.number_ops.number_ops import adjust_number_at, to_base
from je_editor.utils.occurrence.word_occurrences import (
    find_occurrences, replace_whole_word, word_at
)
from je_editor.utils.text_cleanup.text_cleanup import trim_trailing_whitespace
from je_editor.pyside_ui.code.syntax.python_syntax import PythonHighlighter
from je_editor.pyside_ui.dialog.search_ui.search_text_box import SearchBox
from je_editor.pyside_ui.dialog.search_ui.search_replace_widget import SearchReplaceDialog
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.align.align import align_by_delimiter
from je_editor.utils.case_convert.case_convert import (
    to_camel_case, to_kebab_case, to_pascal_case, to_snake_case
)
from je_editor.utils.encode_decode.encode_decode import (
    base64_decode, base64_encode, html_escape, html_unescape,
    json_string_escape, json_string_unescape, url_decode, url_encode
)
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

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


# 行號區域中書籤欄與折疊欄的寬度（像素）
# Width in pixels of the bookmark and fold columns inside the gutter
_BOOKMARK_MARKER_WIDTH = 14
_FOLD_MARKER_WIDTH = 14

# 游標移動幾行以上才視為「跳轉」並記入導覽歷史
# How many lines the caret must move to count as a "jump" recorded in history
_JUMP_THRESHOLD_LINES = 5

# 超過此字元數的文件停用出現次數高亮，避免每次游標移動都掃描整份大檔
# Skip occurrence highlighting past this size, so a large file is not rescanned
# on every caret move
_OCCURRENCE_MAX_CHARS = 100000


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

        # 程式碼折疊與書籤 / Code folding and bookmarks
        self.folding_manager = FoldingManager(self)
        self.bookmark_manager = BookmarkManager(self)
        # 可折疊標頭快取，捲動重繪時免去重複計算；文字變更時失效
        # Cache of foldable header lines so scroll repaints skip recomputation;
        # invalidated whenever the text changes
        self._fold_header_cache: Union[set, None] = None
        self.textChanged.connect(self._on_text_changed_for_features)
        self._register_fold_bookmark_actions()

        # 游標跳轉歷史（上一步／下一步）/ Cursor jump history (back/forward)
        self.location_history = LocationHistory()
        self._last_recorded_line = 0
        # 執行上一步／下一步時暫停記錄，避免把導覽動作本身記進歷史
        # Suppress recording during back/forward so navigation isn't re-recorded
        self._navigating_history = False
        self.cursorPositionChanged.connect(self._record_cursor_jump)
        self._register_history_actions()
        self._register_line_operation_actions()

        # 智慧選取（擴大 / 縮回）/ Smart selection (expand/shrink)
        self.smart_selection_manager = SmartSelectionManager(self)
        self._register_smart_selection_actions()
        self._register_number_actions()

        # 由檔案內容偵測的每檔縮排寬度（None 代表用全域設定）
        # Per-file detected indent width (None means use the global setting)
        self._indent_size_override: Union[int, None] = None

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

    def jump_to_line(self, line: int) -> bool:
        """
        把游標移到指定行並置中顯示
        Move the cursor to a 1-based line number and centre it in the view.

        :param line: 1 起算的行號 / The 1-based line number
        :return: 該行存在並完成跳轉時為 ``True`` / ``True`` when the line exists
        """
        block = self.document().findBlockByNumber(line - 1)
        if not block.isValid():
            return False
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        self.setTextCursor(cursor)
        self.centerCursor()
        self.highlight_current_line()
        return True

    def go_to_line(self) -> None:
        """跳到指定行數 / Go to a specific line number"""
        max_line = self.blockCount()
        line, ok = QInputDialog.getInt(
            self, "Go to Line", f"Line number (1-{max_line}):",
            value=self.textCursor().blockNumber() + 1,
            min=1, max=max_line
        )
        if ok:
            self.jump_to_line(line)

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

    # ── 程式碼折疊與書籤 / Code folding and bookmarks ──────────────

    def _register_fold_bookmark_actions(self) -> None:
        """註冊折疊與書籤的快捷鍵 / Register folding and bookmark shortcuts."""
        for shortcut, handler in (
            ("Ctrl+Shift+[", self.toggle_fold_at_cursor),
            ("Ctrl+Alt+[", self.fold_all),
            ("Ctrl+Alt+]", self.unfold_all),
            ("Ctrl+Alt+K", self.toggle_bookmark),
            ("Ctrl+Alt+L", self.next_bookmark),
            ("Ctrl+Alt+J", self.previous_bookmark),
        ):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            self.addAction(action)

    def _on_text_changed_for_features(self) -> None:
        """
        文字變更時更新折疊與書籤相關狀態
        Update folding-related state when the text changes.
        """
        # 失效可折疊標頭快取，下次繪製時重新計算
        # Invalidate the foldable-header cache so the next paint recomputes it
        self._fold_header_cache = None
        # 只有真的有折疊時才重新套用，避免未折疊時的無謂計算
        # Only re-apply when something is folded, so unfolded editing has no cost
        if self.folding_manager.is_any_folded():
            self.folding_manager.refresh()

    def _foldable_header_lines(self) -> set:
        """取得可折疊標頭行號（快取）/ Foldable header lines (cached)."""
        if self._fold_header_cache is None:
            self._fold_header_cache = self.folding_manager.foldable_header_lines()
        return self._fold_header_cache

    def toggle_fold_at_cursor(self) -> None:
        """切換游標所在區塊的折疊 / Toggle folding of the region at the caret."""
        self.folding_manager.toggle_fold(self.textCursor().blockNumber())
        self.line_number.update()

    def fold_all(self) -> None:
        """折疊所有區塊 / Fold every region."""
        self.folding_manager.fold_all()
        self.line_number.update()

    def unfold_all(self) -> None:
        """展開所有區塊 / Unfold every region."""
        self.folding_manager.unfold_all()
        self.line_number.update()

    def toggle_bookmark(self) -> None:
        """切換游標所在行的書籤 / Toggle the bookmark on the caret line."""
        self.bookmark_manager.toggle_current()
        self.line_number.update()

    def next_bookmark(self) -> None:
        """跳到下一個書籤 / Jump to the next bookmark."""
        self.bookmark_manager.go_to_next()

    def previous_bookmark(self) -> None:
        """跳到上一個書籤 / Jump to the previous bookmark."""
        self.bookmark_manager.go_to_previous()

    # ── 導覽歷史 / Navigation history ─────────────────────────────

    def _register_history_actions(self) -> None:
        """註冊上一步／下一步快捷鍵 / Register back/forward shortcuts."""
        for shortcut, handler in (
            ("Alt+Left", self.navigate_back),
            ("Alt+Right", self.navigate_forward),
        ):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            self.addAction(action)

    def _record_cursor_jump(self) -> None:
        """
        游標大幅移動時記入導覽歷史
        Record a history entry when the caret moves far enough to be a jump.

        跳轉時同時記錄「跳離的位置」與「跳到的位置」，因此「上一步」會回到跳轉前
        的位置，而不是更早的某個紀錄。
        A jump records both the line jumped *from* and the line jumped *to*, so
        "back" returns to where the jump started rather than some earlier entry.
        """
        line = self.textCursor().blockNumber()
        if self._navigating_history:
            self._last_recorded_line = line
            return
        if abs(line - self._last_recorded_line) >= _JUMP_THRESHOLD_LINES:
            self.location_history.visit(self._last_recorded_line)
            self.location_history.visit(line)
        self._last_recorded_line = line

    def navigate_back(self) -> bool:
        """
        回到上一個游標位置
        Jump back to the previous cursor location.

        :return: 有可回退的位置並完成跳轉時為 ``True`` / ``True`` when a jump happened
        """
        return self._go_to_history_line(self.location_history.back())

    def navigate_forward(self) -> bool:
        """
        前進到下一個游標位置
        Jump forward to the next cursor location.

        :return: 有可前進的位置並完成跳轉時為 ``True`` / ``True`` when a jump happened
        """
        return self._go_to_history_line(self.location_history.forward())

    def _go_to_history_line(self, line: Union[int, None]) -> bool:
        """移動游標到歷史中的行，過程中暫停記錄 / Move to a history line without recording."""
        if line is None:
            return False
        block = self.document().findBlockByNumber(line)
        if not block.isValid():
            return False
        self._navigating_history = True
        try:
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()
            self.highlight_current_line()
        finally:
            self._navigating_history = False
        return True

    def gutter_line_at_y(self, y_pos: int) -> int:
        """
        把行號區域的 y 座標對應到區塊行號
        Map a y coordinate in the gutter to a block number.

        :param y_pos: 相對於編輯器視窗的 y 座標 / A y coordinate in the editor viewport
        :return: 對應的區塊行號（0 起算），找不到時回傳 -1
            / The 0-based block number, or -1 when none is found
        """
        block = self.firstVisibleBlock()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid():
            if block.isVisible() and top <= y_pos <= bottom:
                return block.blockNumber()
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            if top > y_pos:
                break
        return -1

    def handle_gutter_click(self, x_pos: int, y_pos: int) -> None:
        """
        處理行號區域的點擊：折疊欄切換折疊、書籤欄切換書籤
        Handle a gutter click: the fold column toggles folding, the bookmark
        column toggles a bookmark.

        :param x_pos: 點擊的 x 座標 / The click x coordinate
        :param y_pos: 點擊的 y 座標 / The click y coordinate
        """
        line = self.gutter_line_at_y(y_pos)
        if line < 0:
            return
        if x_pos <= _BOOKMARK_MARKER_WIDTH:
            self.bookmark_manager.toggle(line)
            self.line_number.update()
            return
        if x_pos >= self.line_number.width() - _FOLD_MARKER_WIDTH:
            if line in self._foldable_header_lines():
                self.folding_manager.toggle_fold(line)
                self.line_number.update()

    def line_number_paint(self, event: QtGui.QPaintEvent) -> None:
        """
        繪製行號區域，包含書籤與折疊標記
        Paint the gutter, including bookmark and fold markers.
        """
        painter = QPainter(self.line_number)
        # 填滿背景色
        painter.fillRect(event.rect(), actually_color_dict.get("line_number_background_color"))

        bookmarked = set(self.bookmark_manager.bookmarked_lines())
        fold_headers = self._foldable_header_lines()
        folded_headers = self.folding_manager.folded_header_lines()
        gutter_width = self.line_number.width()
        line_height = self.fontMetrics().height()

        # 從第一個可見區塊開始
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # 逐行繪製行號
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(actually_color_dict.get("line_number_color"))
                painter.drawText(
                    _BOOKMARK_MARKER_WIDTH,
                    int(top),
                    gutter_width - _BOOKMARK_MARKER_WIDTH - _FOLD_MARKER_WIDTH,
                    line_height,
                    Qt.AlignmentFlag.AlignCenter,
                    str(block_number + 1),
                )
                if block_number in bookmarked:
                    self._paint_bookmark_marker(painter, top, line_height)
                if block_number in fold_headers:
                    self._paint_fold_marker(
                        painter, top, line_height, gutter_width,
                        collapsed=block_number in folded_headers)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def _paint_bookmark_marker(self, painter: QPainter, top: float, line_height: int) -> None:
        """在行號左側繪製書籤圓點 / Draw the bookmark dot on the gutter's left."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = actually_color_dict.get("bookmark_marker_color")
        painter.setBrush(color)
        painter.setPen(color)
        radius = max(3, line_height // 4)
        center_y = int(top) + line_height // 2
        painter.drawEllipse(
            _BOOKMARK_MARKER_WIDTH // 2 - radius, center_y - radius, radius * 2, radius * 2)
        painter.restore()

    def _paint_fold_marker(
            self, painter: QPainter, top: float, line_height: int,
            gutter_width: int, collapsed: bool) -> None:
        """在行號右側繪製折疊三角形 / Draw the fold triangle on the gutter's right."""
        painter.save()
        painter.setPen(actually_color_dict.get("fold_marker_color"))
        marker = "▸" if collapsed else "▾"
        painter.drawText(
            gutter_width - _FOLD_MARKER_WIDTH,
            int(top),
            _FOLD_MARKER_WIDTH,
            line_height,
            Qt.AlignmentFlag.AlignCenter,
            marker,
        )
        painter.restore()

    def line_number_width(self) -> int:
        """
        計算行號區域寬度（含書籤與折疊欄）
        Calculate gutter width, including the bookmark and fold columns.
        """
        digits = len(str(self.blockCount()))  # 根據總行數決定位數
        return 12 * digits + _BOOKMARK_MARKER_WIDTH + _FOLD_MARKER_WIDTH

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

        self._append_occurrence_selections(selections, text, pos)
        self.setExtraSelections(selections)

    def word_occurrences_under_cursor(self, text: str, position: int) -> list[int]:
        """
        取得游標所在字詞在文件中的所有出現位置
        Return every occurrence position of the word under the caret.

        字詞過大檔案、單一出現或非識別字時回傳空清單，因此不會產生無意義的高亮。
        Returns an empty list for large files, a lone occurrence, or a non-identifier,
        so no pointless highlight is produced.

        :param text: 文件內容 / The document text
        :param position: 游標字元位置 / The caret character position
        :return: 出現位置清單（兩個以上才回傳）/ Occurrence positions (only when 2+)
        """
        if len(text) > _OCCURRENCE_MAX_CHARS:
            return []
        found = word_at(text, position)
        if found is None:
            return []
        word, _start, _end = found
        positions = find_occurrences(text, word)
        # 只有一個出現時不必高亮 / A single occurrence needs no highlight
        return positions if len(positions) > 1 else []

    def _append_occurrence_selections(self, selections: list, text: str, position: int) -> None:
        """把游標所在字詞的所有出現位置加入高亮 / Append occurrence highlights."""
        positions = self.word_occurrences_under_cursor(text, position)
        if not positions:
            return
        found = word_at(text, position)
        if found is None:
            return
        word_length = len(found[0])
        occurrence_fmt = QTextCharFormat()
        occurrence_fmt.setBackground(actually_color_dict.get("occurrence_highlight_color"))
        doc = self.document()
        for start in positions:
            selection = QTextEdit.ExtraSelection()
            cursor = QTextCursor(doc)
            cursor.setPosition(start)
            cursor.setPosition(start + word_length, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            selection.format = occurrence_fmt
            selections.append(selection)

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
        複製當前行或選取內容 (Ctrl+D)
        Duplicate the current line, or the selection when there is one.

        有選取時在選取結尾後插入一份相同內容，並讓游標選住新複本；沒有選取時
        複製整行。整個動作為單一復原步驟。
        With a selection, a copy is inserted right after it and the caret selects the
        new copy; without one, the whole line is duplicated. The whole action is a
        single undo step.
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            self._duplicate_selection(cursor)
            return
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        line_text = cursor.selectedText()
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
        cursor.insertText("\n" + line_text)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _duplicate_selection(self, cursor: QTextCursor) -> None:
        """在選取結尾後插入一份複本並選住它 / Insert a copy after the selection and select it."""
        selected_text = cursor.selectedText()
        end = cursor.selectionEnd()
        cursor.beginEditBlock()
        cursor.setPosition(end)
        cursor.insertText(selected_text)
        cursor.endEditBlock()
        # 讓游標選住剛插入的複本 / Select the copy that was just inserted
        cursor.setPosition(end)
        cursor.setPosition(end + len(selected_text), QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

    # ── 智慧選取 / Smart selection ───────────────────────────────

    def _register_smart_selection_actions(self) -> None:
        """註冊智慧選取快捷鍵 / Register smart selection shortcuts."""
        for shortcut, handler in (
            ("Ctrl+Alt+Right", self.expand_selection),
            ("Ctrl+Alt+Left", self.shrink_selection),
        ):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            self.addAction(action)

    def expand_selection(self) -> None:
        """把選取擴大到下一個更大的範圍 / Expand the selection to the next larger range."""
        self.smart_selection_manager.expand()

    def shrink_selection(self) -> None:
        """縮回上一個較小的選取範圍 / Shrink back to the previous smaller range."""
        self.smart_selection_manager.shrink()

    # ── 游標處數字加減 / Increment / decrement the number under the caret ──

    def _register_number_actions(self) -> None:
        """註冊數字加減快捷鍵 / Register number increment/decrement shortcuts."""
        for shortcut, delta in (("Ctrl+Alt+Up", 1), ("Ctrl+Alt+Down", -1)):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(lambda checked=False, step=delta: self.adjust_number(step))
            self.addAction(action)
        rename_action = QAction(self)
        rename_action.setShortcut("F2")
        rename_action.triggered.connect(self.rename_word_under_cursor)
        self.addAction(rename_action)

    def rename_word_under_cursor(self) -> bool:
        """
        重新命名游標所在識別字在整個檔案中的所有出現（整字比對，單一復原）
        Rename every whole-word occurrence of the identifier under the caret across
        the file (word-boundary match, single undo step).

        這是「文字層級」的重新命名：以字界比對，因此不會動到部分符合的字詞，但字串
        與註解中剛好同名的字也會一併替換。會彈出對話框詢問新名稱。
        This is a *textual* rename: word boundaries protect partial matches, but a
        same-named word inside a string or comment is replaced too. A dialog asks for
        the new name.

        :return: 有實際重新命名時為 ``True`` / ``True`` when a rename actually happened
        """
        text = self.toPlainText()
        found = word_at(text, self.textCursor().position())
        if found is None or not found[0].isidentifier():
            return False
        old_word = found[0]
        word_dict = language_wrapper.language_word_dict
        new_word, accepted = QInputDialog.getText(
            self,
            word_dict.get("rename_dialog_title"),
            word_dict.get("rename_dialog_label").format(word=old_word),
            text=old_word,
        )
        new_word = new_word.strip()
        if not accepted or not new_word or new_word == old_word:
            return False
        return self._replace_document_text(replace_whole_word(text, old_word, new_word))

    def adjust_number(self, delta: int) -> bool:
        """
        把游標所在的整數加上 ``delta``（單一復原步驟）
        Add ``delta`` to the integer under the caret as one undo step.

        :param delta: 增減量（可為負）/ The amount to add (may be negative)
        :return: 游標在數字上並完成調整時為 ``True`` / ``True`` when a number was adjusted
        """
        result = adjust_number_at(self.toPlainText(), self.textCursor().position(), delta)
        if result is None:
            return False
        new_text, start, end = result
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(new_text)
        cursor.endEditBlock()
        caret = self.textCursor()
        caret.setPosition(start + len(new_text))
        self.setTextCursor(caret)
        return True

    # ── 行操作 / Line operations ─────────────────────────────────

    def _register_line_operation_actions(self) -> None:
        """註冊行操作快捷鍵 / Register line-operation shortcuts."""
        for shortcut, handler in (
            ("Ctrl+Shift+D", self.delete_current_line),
            ("Ctrl+Shift+J", self.join_selected_lines),
            ("Ctrl+Alt+S", self.sort_selected_lines),
        ):
            action = QAction(self)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            self.addAction(action)

    def _selected_block_range(self, cursor: QTextCursor) -> tuple[int, int]:
        """取得選取（或游標所在）涵蓋的 block 區間 / The block range covered by the selection."""
        if cursor.hasSelection():
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            probe = QTextCursor(self.document())
            probe.setPosition(start)
            start_block = probe.blockNumber()
            probe.setPosition(end)
            end_block = probe.blockNumber()
            # 選取剛好停在行首時，不把下一行算進來 / Don't include a line the selection only touches at its start
            if end_block > start_block and probe.positionInBlock() == 0:
                end_block -= 1
            return start_block, end_block
        return cursor.blockNumber(), cursor.blockNumber()

    def _replace_block_range(self, start_block: int, end_block: int, new_text: str) -> None:
        """以新文字取代指定 block 區間 / Replace a block range with new text as one undo step."""
        document = self.document()
        start_cursor = QTextCursor(document.findBlockByNumber(start_block))
        start_cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        end_block_obj = document.findBlockByNumber(end_block)
        start_cursor.setPosition(
            end_block_obj.position() + end_block_obj.length() - 1,
            QTextCursor.MoveMode.KeepAnchor)
        start_cursor.insertText(new_text)

    def delete_current_line(self) -> None:
        """
        刪除目前行或選取涵蓋的行 (Ctrl+Shift+D)
        Delete the current line, or every line the selection touches.

        一併移除該行的換行：中間的行連同其後的換行刪除；刪到最後一行時，改為連同
        其前的換行刪除，避免留下多餘空行。
        The line's newline goes too: an interior line takes the newline after it,
        while deleting through the last line takes the newline before it instead,
        so no stray blank line is left behind.
        """
        cursor = self.textCursor()
        start_block, end_block = self._selected_block_range(cursor)
        document = self.document()
        first_block = document.findBlockByNumber(start_block)
        last_block = document.findBlockByNumber(end_block)
        next_block = last_block.next()

        delete_cursor = QTextCursor(document)
        if next_block.isValid():
            delete_cursor.setPosition(first_block.position())
            delete_cursor.setPosition(next_block.position(), QTextCursor.MoveMode.KeepAnchor)
        else:
            # 最後一行：把前一行的換行也吃掉 / Last line: also consume the preceding newline
            start_position = first_block.position()
            if start_position > 0:
                start_position -= 1
            delete_cursor.setPosition(start_position)
            delete_cursor.setPosition(
                last_block.position() + last_block.length() - 1,
                QTextCursor.MoveMode.KeepAnchor)
        delete_cursor.removeSelectedText()
        self.highlight_current_line()

    def _transform_selected_lines(self, transform) -> bool:
        """
        對選取涵蓋的行套用一個 list[str] → list[str] 的轉換
        Apply a ``list[str] -> list[str]`` transform to the lines the selection spans.

        少於兩行時不做任何事（排序、去重、反轉在單行都沒有意義）。
        Does nothing with fewer than two lines (sorting, dedup and reversing are all
        meaningless for a single line).

        :param transform: 行轉換函式 / The line transform
        :return: 有套用時為 ``True`` / ``True`` when the transform was applied
        """
        cursor = self.textCursor()
        start_block, end_block = self._selected_block_range(cursor)
        if end_block <= start_block:
            return False
        lines = self._block_texts(start_block, end_block)
        self._replace_block_range(start_block, end_block, "\n".join(transform(lines)))
        return True

    def sort_selected_lines(self) -> None:
        """
        排序選取的行 (Ctrl+Alt+S)
        Sort the selected lines alphabetically.
        """
        self._transform_selected_lines(sort_lines)

    def remove_duplicate_selected_lines(self) -> None:
        """
        移除選取範圍內的重複行，保留首次出現順序
        Remove duplicate lines within the selection, keeping first-seen order.
        """
        self._transform_selected_lines(unique_lines)

    def reverse_selected_lines(self) -> None:
        """
        反轉選取範圍內的行順序
        Reverse the order of the selected lines.
        """
        self._transform_selected_lines(reverse_lines)

    def natural_sort_selected_lines(self) -> None:
        """
        以自然順序排序選取的行（item2 在 item10 之前）
        Sort the selected lines naturally (item2 before item10).
        """
        self._transform_selected_lines(natural_sort)

    def remove_blank_selected_lines(self) -> None:
        """
        移除選取範圍內的空白行
        Remove blank lines within the selection.
        """
        self._transform_selected_lines(remove_blank_lines)

    def align_selected_lines(self) -> None:
        """
        依使用者輸入的分隔符對齊選取的行
        Align the selected lines on a delimiter the user types.

        彈出對話框詢問分隔符（預設 ``=``），把每行第一個該分隔符對齊到同一欄。
        A dialog asks for the delimiter (default ``=``) and aligns each line's first
        occurrence of it into the same column.
        """
        word_dict = language_wrapper.language_word_dict
        delimiter, accepted = QInputDialog.getText(
            self,
            word_dict.get("align_dialog_title"),
            word_dict.get("align_dialog_label"),
            text="=",
        )
        if not accepted or delimiter == "":
            return
        self._transform_selected_lines(lambda lines: align_by_delimiter(lines, delimiter))

    def _transform_selection_text(self, transform) -> bool:
        """
        對選取的文字套用一個 str → str 的轉換並保留選取
        Apply a ``str -> str`` transform to the selected text, keeping it selected.

        :param transform: 文字轉換函式 / The text transform
        :return: 有選取並套用時為 ``True`` / ``True`` when there was a selection to transform
        """
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return False
        start = cursor.selectionStart()
        new_text = transform(cursor.selectedText())
        # 轉換回傳 None（例如解碼失敗）時保持原樣不動 / A None result (e.g. failed decode) is a no-op
        if new_text is None:
            return False
        cursor.beginEditBlock()
        cursor.insertText(new_text)
        cursor.endEditBlock()
        cursor.setPosition(start)
        cursor.setPosition(start + len(new_text), QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)
        return True

    def uppercase_selection(self) -> None:
        """把選取文字轉為大寫 / Convert the selected text to uppercase."""
        self._transform_selection_text(str.upper)

    def lowercase_selection(self) -> None:
        """把選取文字轉為小寫 / Convert the selected text to lowercase."""
        self._transform_selection_text(str.lower)

    def base64_encode_selection(self) -> None:
        """把選取文字做 Base64 編碼 / Base64-encode the selected text."""
        self._transform_selection_text(base64_encode)

    def base64_decode_selection(self) -> None:
        """把選取文字做 Base64 解碼（失敗則不動）/ Base64-decode the selection (no-op on failure)."""
        self._transform_selection_text(base64_decode)

    def url_encode_selection(self) -> None:
        """把選取文字做 URL 編碼 / URL-encode the selected text."""
        self._transform_selection_text(url_encode)

    def url_decode_selection(self) -> None:
        """把選取文字做 URL 解碼 / URL-decode the selected text."""
        self._transform_selection_text(url_decode)

    def html_escape_selection(self) -> None:
        """把選取文字做 HTML 轉義 / HTML-escape the selected text."""
        self._transform_selection_text(html_escape)

    def html_unescape_selection(self) -> None:
        """把選取文字做 HTML 還原 / HTML-unescape the selected text."""
        self._transform_selection_text(html_unescape)

    def json_escape_selection(self) -> None:
        """把選取文字轉成 JSON 字串字面值 / Escape the selection into a JSON string literal."""
        self._transform_selection_text(json_string_escape)

    def json_unescape_selection(self) -> None:
        """把選取的 JSON 字串還原（失敗則不動）/ Unescape a JSON string (no-op on failure)."""
        self._transform_selection_text(json_string_unescape)

    def swapcase_selection(self) -> None:
        """把選取文字大小寫互換 / Swap the case of the selected text."""
        self._transform_selection_text(str.swapcase)

    def titlecase_selection(self) -> None:
        """把選取文字轉為標題大小寫 / Convert the selected text to title case."""
        self._transform_selection_text(str.title)

    def to_snake_case_selection(self) -> None:
        """把選取的識別字轉為 snake_case / Convert the selection to snake_case."""
        self._transform_selection_text(to_snake_case)

    def to_camel_case_selection(self) -> None:
        """把選取的識別字轉為 camelCase / Convert the selection to camelCase."""
        self._transform_selection_text(to_camel_case)

    def to_pascal_case_selection(self) -> None:
        """把選取的識別字轉為 PascalCase / Convert the selection to PascalCase."""
        self._transform_selection_text(to_pascal_case)

    def to_kebab_case_selection(self) -> None:
        """把選取的識別字轉為 kebab-case / Convert the selection to kebab-case."""
        self._transform_selection_text(to_kebab_case)

    def number_to_hex_selection(self) -> None:
        """把選取的整數轉為十六進位（失敗則不動）/ Convert the selected integer to hex."""
        self._transform_selection_text(lambda text: to_base(text, 16))

    def number_to_decimal_selection(self) -> None:
        """把選取的整數轉為十進位（失敗則不動）/ Convert the selected integer to decimal."""
        self._transform_selection_text(lambda text: to_base(text, 10))

    def number_to_binary_selection(self) -> None:
        """把選取的整數轉為二進位（失敗則不動）/ Convert the selected integer to binary."""
        self._transform_selection_text(lambda text: to_base(text, 2))

    def join_selected_lines(self) -> None:
        """
        把選取的行併成一行 (Ctrl+Shift+J)
        Join the selected lines into a single line.
        """
        cursor = self.textCursor()
        start_block, end_block = self._selected_block_range(cursor)
        if end_block <= start_block:
            return
        lines = self._block_texts(start_block, end_block)
        self._replace_block_range(start_block, end_block, join_lines(lines))

    def _block_texts(self, start_block: int, end_block: int) -> list[str]:
        """取得指定 block 區間的每一行文字 / The text of each block in the range."""
        document = self.document()
        return [
            document.findBlockByNumber(number).text()
            for number in range(start_block, end_block + 1)
        ]

    def _replace_document_text(self, new_text: str) -> bool:
        """
        以新內容取代整份文件（單一復原步驟，並還原游標）
        Replace the whole document as one undo step, restoring the caret.

        :param new_text: 新的完整內容 / The new full content
        :return: 有變動時為 ``True`` / ``True`` when the content changed
        """
        if new_text == self.toPlainText():
            return False
        cursor = self.textCursor()
        line = cursor.blockNumber()
        column = cursor.positionInBlock()

        edit_cursor = self.textCursor()
        edit_cursor.beginEditBlock()
        edit_cursor.select(QTextCursor.SelectionType.Document)
        edit_cursor.insertText(new_text)
        edit_cursor.endEditBlock()

        self._restore_caret(line, column)
        return True

    def convert_indentation_to_spaces(self, tab_size: int = 4) -> bool:
        """
        把整份文件開頭縮排的 Tab 轉成空白 / Convert leading tabs to spaces document-wide.

        :param tab_size: 每個 Tab 對應的空白數 / Spaces per tab
        :return: 有變動時為 ``True`` / ``True`` when the content changed
        """
        return self._replace_document_text(
            convert_leading_tabs_to_spaces(self.toPlainText(), tab_size))

    def convert_indentation_to_tabs(self, tab_size: int = 4) -> bool:
        """
        把整份文件開頭縮排的空白轉成 Tab / Convert leading spaces to tabs document-wide.

        :param tab_size: 每個 Tab 對應的空白數 / Spaces per tab
        :return: 有變動時為 ``True`` / ``True`` when the content changed
        """
        return self._replace_document_text(
            convert_leading_spaces_to_tabs(self.toPlainText(), tab_size))

    def trim_trailing_whitespace_document(self) -> bool:
        """
        移除整份文件每行結尾的空白（單一復原步驟）
        Strip trailing whitespace across the whole document as one undo step.

        內容沒有變動時不做任何事，也不會產生多餘的復原步驟；有變動時盡量把游標
        還原到原本的行與欄（欄位超過新行長度時夾到行尾）。
        Does nothing when the content is unchanged (no stray undo step); otherwise
        restores the caret to its original line and column, clamped to the new line
        length.

        :return: 有實際修改時為 ``True`` / ``True`` when the text actually changed
        """
        return self._replace_document_text(trim_trailing_whitespace(self.toPlainText()))

    def _restore_caret(self, line: int, column: int) -> None:
        """把游標還原到指定行與欄，欄位夾到行尾 / Restore the caret, clamping the column."""
        block = self.document().findBlockByNumber(line)
        if not block.isValid():
            return
        cursor = self.textCursor()
        cursor.setPosition(block.position() + min(column, len(block.text())))
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

    def indent_size(self) -> int:
        """
        取得目前生效的縮排空白數
        Return the indent width in spaces currently in effect.

        優先使用本編輯器由檔案內容偵測到的縮排（per-editor override），沒有時退回
        ``user_setting_dict['indent_size']``（預設 4）。因此 Tab 縮排、取消縮排與
        Enter 自動縮排都遵循同一個值。
        Prefers this editor's per-file detected indent (an override); otherwise falls
        back to ``user_setting_dict['indent_size']`` (default 4). Tab-indent, unindent
        and Enter auto-indent all follow the same value.

        :return: 縮排空白數（1 到 16）/ The indent width in spaces (1 to 16)
        """
        override = getattr(self, "_indent_size_override", None)
        if isinstance(override, int) and 1 <= override <= 16:
            return override
        from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
        size = user_setting_dict.get("indent_size", 4)
        if not isinstance(size, int) or size < 1:
            return 4
        return min(size, 16)

    def apply_detected_indentation(self) -> int | None:
        """
        依目前內容偵測縮排寬度並套用到本編輯器
        Detect the indent width from the current content and apply it to this editor.

        偵測到以空白縮排時，設定 per-editor 覆寫值並更新 Tab 顯示寬度；以 Tab 縮排
        或無法判斷時清除覆寫，改用全域設定。永不修改文字內容。
        On space indentation, sets the per-editor override and updates the visual tab
        width; on tab indentation or when undecidable, clears the override to fall
        back to the global setting. It never modifies the text.

        :return: 套用的縮排空白數，未套用時回傳 ``None``
            / The applied indent width, or ``None`` when not applied
        """
        text = self.toPlainText()
        if detect_indentation_uses_tabs(text):
            self._indent_size_override = None
            return None
        width = detect_indent_width(text)
        self._indent_size_override = width if width and 1 <= width <= 16 else None
        if self._indent_size_override is not None:
            self.setTabStopDistance(
                QtGui.QFontMetricsF(self.font()).horizontalAdvance(
                    " " * self._indent_size_override))
        return self._indent_size_override

    def _unindent_current_block(self, cursor: QTextCursor) -> None:
        """移除當前行開頭最多一個縮排單位的空白 / Remove up to one indent unit of leading spaces."""
        spaces = self._leading_space_count(cursor.block().text(), limit=self.indent_size())
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

        indent_unit = " " * self.indent_size()
        cursor.setPosition(start)
        for _ in range(end_block - start_block + 1):
            cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
            if indent:
                cursor.insertText(indent_unit)
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
            indent += " " * self.indent_size()
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

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        點擊行號區域時切換折疊或書籤
        Toggle folding or a bookmark when the gutter is clicked.
        """
        position = event.position()
        self.editor.handle_gutter_click(int(position.x()), int(position.y()))

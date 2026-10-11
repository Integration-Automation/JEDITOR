"""
待辦事項面板：列出專案中所有 TODO / FIXME 註解
TODO panel: list every TODO / FIXME comment in the project.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget
)

from je_editor.pyside_ui.main_ui.workspace.workspace_roots import (
    labelled_root_paths, primary_root_path
)
from je_editor.utils.file_scan.todo_scanner import DEFAULT_TAGS, TodoItem
from je_editor.utils.file_scan.workspace_scan import (
    FoundTodo, LabelledRoot, as_labelled_roots, scan_workspace_todos
)
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 「全部標籤」的篩選值 / Filter value meaning "every tag"
ALL_TAGS_FILTER = "*"
# 樹狀清單欄位索引 / Column indexes in the tree
COLUMN_TAG = 0
COLUMN_MESSAGE = 1
COLUMN_FILE = 2
COLUMN_LINE = 3
# 訊息欄的預設寬度 / Default width of the message column
MESSAGE_COLUMN_WIDTH = 420


class TodoScanThread(QThread):
    """
    背景掃描專案中的 TODO 註解
    Scan the project for TODO comments in the background.
    """

    scanned = Signal(list)  # list[TodoItem]

    def __init__(self, root: str | list[LabelledRoot]) -> None:
        """
        :param root: 要掃描的專案根目錄；工作區有好幾個根目錄時是「顯示名稱與路徑」的清單
            / The project root to scan, or each root's label and path when the
            workspace has several
        """
        super().__init__()
        # 具名執行緒：萬一它在執行中被銷毀，Qt 的中止訊息才說得出是哪一條
        # A named thread, so Qt's abort message says which one if it is ever
        # destroyed while still running
        self.setObjectName("TodoScanThread")
        self._roots = as_labelled_roots(root)
        self._stop_requested = False
        # 掃描結果，含開檔用的完整路徑；在送出 scanned 之前就填好
        # What the scan found, full paths included; filled before scanned is emitted
        self.found: list[FoundTodo] = []

    def stop(self) -> None:
        """要求提前結束掃描 / Ask the scan to finish early."""
        self._stop_requested = True

    def run(self) -> None:
        """執行掃描並送出結果 / Run the scan and emit the result."""
        try:
            found = scan_workspace_todos(
                self._roots, should_stop=lambda: self._stop_requested)
        except OSError as error:
            jeditor_logger.error(f"todo_panel_widget.py scan failed: {error!r}")
            found = []
        self.found = found
        self.scanned.emit([entry.item for entry in found])


class TodoPanelWidget(QWidget):
    """
    待辦事項面板
    The TODO panel.

    掃描在背景執行緒中進行，雙擊項目會在編輯器中開啟該行。
    Scanning runs in a worker thread; double-clicking a row opens that line.
    """

    def __init__(self, main_window=None, root: str | None = None) -> None:
        """
        :param main_window: 用來開檔的主視窗 / The window used to open files
        :param root: 專案根目錄，``None`` 時掃描視窗工作區的每個根目錄
            / The project root; ``None`` scans every root of the window's workspace
        """
        super().__init__()
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        self._root = root
        self._items: list[TodoItem] = []
        # 每筆項目開檔用的完整路徑，以（顯示路徑, 行號）為鍵
        # The full path to open each item by, keyed by (shown path, line)
        self._full_paths: dict[tuple[str, int], str] = {}
        self._scan_thread: TodoScanThread | None = None

        self.refresh_button = QPushButton(word.get("todo_panel_refresh"))
        self.refresh_button.clicked.connect(self.start_scan)

        self.tag_filter = QComboBox()
        self.tag_filter.addItem(word.get("todo_panel_all_tags"), ALL_TAGS_FILTER)
        for tag in DEFAULT_TAGS:
            self.tag_filter.addItem(tag, tag)
        self.tag_filter.currentIndexChanged.connect(self._render_items)

        self.status_label = QLabel(word.get("todo_panel_ready"))

        self.result_tree = QTreeWidget()
        self.result_tree.setColumnCount(4)
        self.result_tree.setHeaderLabels([
            word.get("todo_panel_col_tag"),
            word.get("todo_panel_col_message"),
            word.get("todo_panel_col_file"),
            word.get("todo_panel_col_line"),
        ])
        self.result_tree.setColumnWidth(COLUMN_MESSAGE, MESSAGE_COLUMN_WIDTH)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemDoubleClicked.connect(self._open_item)

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.tag_filter)
        controls.addWidget(self.status_label)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.result_tree)
        self.setLayout(layout)

        self.start_scan()

    def start_scan(self) -> None:
        """
        啟動一次背景掃描
        Kick off one background scan.

        掃描進行中重複觸發會被忽略，避免覆寫仍在執行的 QThread。
        A re-entrant trigger is ignored so a still-running QThread is never dropped.
        """
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.status_label.setText(language_wrapper.language_word_dict.get("todo_panel_scanning"))
        # 沒有指定根目錄時每次掃描都重新問工作區，之後加進來的根目錄才掃得到
        # With no root given, the workspace is asked afresh for each scan, so a
        # root added later is scanned too
        roots = self._root if self._root is not None else labelled_root_paths(self._main_window)
        self._scan_thread = TodoScanThread(roots)
        self._scan_thread.scanned.connect(self._on_scanned)
        self._scan_thread.start()

    def visible_items(self) -> list[TodoItem]:
        """
        取得目前篩選條件下的項目
        Return the items matching the current tag filter.

        :return: 篩選後的項目 / The filtered items
        """
        selected = self.tag_filter.currentData()
        if selected in (None, ALL_TAGS_FILTER):
            return list(self._items)
        return [item for item in self._items if item.tag == selected]

    def _on_scanned(self, items: list) -> None:
        """掃描完成後更新畫面 / Update the view once the scan finishes."""
        jeditor_logger.info(f"todo_panel_widget.py scanned {len(items)} todo items")
        self._items = items
        found = self._scan_thread.found if self._scan_thread is not None else []
        self._full_paths = {
            (entry.item.path, entry.item.line): entry.full_path for entry in found}
        self.refresh_button.setEnabled(True)
        self._render_items()

    def retranslate(self) -> None:
        """
        換語言後重新標示自己
        Relabel after the language changes.

        標籤篩選的第一項是「所有標籤」，其餘是掃到的標籤本身（TODO、FIXME），那些
        不是翻譯來的，不能動。
        The first entry in the tag filter is "all tags" and the rest are the tags
        as found in the code (TODO, FIXME); those did not come from a translation
        and are left alone.
        """
        word = language_wrapper.language_word_dict
        self.refresh_button.setText(word.get("todo_panel_refresh"))
        self.tag_filter.setItemText(0, word.get("todo_panel_all_tags"))
        self.result_tree.setHeaderLabels([
            word.get("todo_panel_col_tag"),
            word.get("todo_panel_col_message"),
            word.get("todo_panel_col_file"),
            word.get("todo_panel_col_line"),
        ])
        self._render_items()

    def _render_items(self) -> None:
        """依篩選條件重建清單 / Rebuild the tree for the current filter."""
        visible = self.visible_items()
        self.result_tree.clear()
        for item in visible:
            row = QTreeWidgetItem([item.tag, item.message, item.path, str(item.line)])
            row.setData(COLUMN_TAG, Qt.ItemDataRole.UserRole, item)
            self.result_tree.addTopLevelItem(row)
        self.status_label.setText(
            language_wrapper.language_word_dict.get("todo_panel_found").format(count=len(visible)))

    def _open_item(self, row: QTreeWidgetItem, _column: int) -> None:
        """在編輯器中開啟被雙擊的項目 / Open the double-clicked item in the editor."""
        item = row.data(COLUMN_TAG, Qt.ItemDataRole.UserRole)
        if item is None:
            return
        full_path = self._full_paths.get((item.path, item.line))
        if full_path is not None:
            open_todo_at(self._main_window, full_path, item.line)

    def closeEvent(self, event) -> None:
        """
        關閉前停掉掃描執行緒
        Stop the scan thread before the panel goes away.

        先擋掉信號再等待，避免執行緒在物件已銷毀後才送出結果。
        Signals are blocked before waiting so a late result cannot reach a dead
        widget, and waiting keeps the QThread from being destroyed while running.
        """
        thread = self._scan_thread
        if thread is not None and thread.isRunning():
            thread.blockSignals(True)
            thread.stop()
            thread.wait()
        super().closeEvent(event)


def resolve_todo_root(main_window) -> str:
    """
    取得要掃描的專案根目錄
    Resolve the project root that should be scanned.

    :param main_window: 主編輯器視窗，可為 ``None`` / The main window, may be ``None``
    :return: 專案根目錄路徑 / The project root path
    """
    return primary_root_path(main_window)


def open_todo_item(main_window, root: str, item: TodoItem) -> bool:
    """
    在編輯器中開啟一筆待辦事項所在的行
    Open the line a TODO item points at.

    :param main_window: 用來開檔的主視窗 / The window used to open files
    :param root: 專案根目錄 / The project root
    :param item: 要開啟的項目 / The item to open
    :return: 成功要求開檔時為 ``True`` / ``True`` when the open was requested
    """
    return open_todo_at(main_window, Path(root) / item.path, item.line)


def open_todo_at(main_window, full_path: str | Path, line: int) -> bool:
    """
    在編輯器中開啟某個檔案的某一行
    Open one line of a file in the editor.

    :param main_window: 用來開檔的主視窗 / The window used to open files
    :param full_path: 檔案的完整路徑 / The file's full path
    :param line: 1 起算的行號 / The 1-based line number
    :return: 成功要求開檔時為 ``True`` / ``True`` when the open was requested
    """
    if main_window is None or not hasattr(main_window, "go_to_new_tab"):
        return False
    main_window.go_to_new_tab(Path(full_path))
    jump_to_item_line(main_window, line)
    return True


def jump_to_item_line(main_window, line: int) -> bool:
    """
    把目前分頁的游標移到指定行
    Move the current tab's cursor to a line.

    :param main_window: 主編輯器視窗 / The main editor window
    :param line: 1 起算的行號 / The 1-based line number
    :return: 成功跳轉時為 ``True`` / ``True`` when the jump happened
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return False
    widget = tab_widget.currentWidget()
    if not isinstance(widget, EditorWidget):
        return False
    return widget.code_edit.jump_to_line(line)

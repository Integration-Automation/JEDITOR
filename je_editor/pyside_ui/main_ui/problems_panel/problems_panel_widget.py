"""
問題面板：列出目前分頁的 lint 診斷
Problems panel: list the lint diagnostics of the current tab.

診斷是由編輯器在背景檢查後持有的，面板只負責顯示與跳轉，不自己執行 linter。
The editor already holds the diagnostics from its background check; the panel
only displays them and jumps to a line, never running the linter itself.

ruff 與語言伺服器的診斷都以統一模型放進同一個 ``DiagnosticStore``，所以嚴重度與
來源的篩選對兩者一視同仁，清單的順序也固定。
ruff's findings and a language server's go into one ``DiagnosticStore`` in the
unified model, so the severity and source filters treat both alike and the list
always comes out in the same order.
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.code_scan.ruff_lint import RUFF_SOURCE, apply_fixes
from je_editor.core.diagnostics.diagnostic_model import Diagnostic, DiagnosticStore, Severity
from je_editor.core.diagnostics.legacy_diagnostics import unify
from je_editor.core.uri.resource_uri import to_path, to_uri, uri_key
from je_editor.pyside_ui.main_ui.problems_panel.project_lint_worker import (
    ProjectLintWorker
)
from je_editor.utils.file.open.open_file import read_file_with_encoding
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 樹狀清單欄位索引 / Column indexes in the tree
COLUMN_CODE = 0
COLUMN_MESSAGE = 1
COLUMN_LINE = 2
COLUMN_FILE = 3
COLUMN_SEVERITY = 4
COLUMN_SOURCE = 5
# 訊息欄的預設寬度 / Default width of the message column
MESSAGE_COLUMN_WIDTH = 460
# 「全部嚴重度」的篩選值 / Filter value meaning "every severity"
ALL_SEVERITIES = "*"
# 「全部來源」的篩選值 / Filter value meaning "every source"
ALL_SOURCES = "*"
# 各欄標題的字典鍵，依欄位順序 / The dictionary key of each column's title, in column order
_COLUMN_TITLE_KEYS = (
    "problems_panel_col_code",
    "problems_panel_col_message",
    "problems_panel_col_line",
    "problems_panel_col_file",
    "problems_panel_col_severity",
    "problems_panel_col_source",
)
# 各嚴重度名稱的字典鍵 / The dictionary key of each severity's name
_SEVERITY_NAME_KEYS = {
    Severity.ERROR: "problems_panel_severity_error",
    Severity.WARNING: "problems_panel_severity_warning",
    Severity.INFORMATION: "problems_panel_severity_information",
    Severity.HINT: "problems_panel_severity_hint",
}


def current_code_editor(main_window):
    """
    取得目前分頁的程式碼編輯器
    Return the code editor of the current tab.

    :param main_window: 主編輯器視窗 / the main editor window
    :return: 編輯器，目前分頁不是編輯器時為 ``None`` / the editor, or ``None``
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return None
    widget = tab_widget.currentWidget()
    return widget.code_edit if isinstance(widget, EditorWidget) else None


class ProblemsPanelWidget(QWidget):
    """
    顯示目前檔案的 lint 診斷
    Show the lint diagnostics of the file in the current tab.
    """

    def __init__(self, main_window=None) -> None:
        """
        :param main_window: 用來取得目前編輯器的主視窗 / the window holding the tabs
        """
        super().__init__()
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        # 面板目前顯示的所有診斷，依「來源 × 資源」存放
        # Everything the panel is showing, kept per source and per resource
        self._store = DiagnosticStore()
        # 專案檢查在工作執行緒進行，這裡持有進行中的那一個
        # The project check runs on a worker thread; this holds the one in flight
        self._project_worker: ProjectLintWorker | None = None

        self.refresh_button = QPushButton(word.get("problems_panel_refresh"))
        self.refresh_button.clicked.connect(self.refresh)
        self.project_check = QCheckBox(word.get("problems_panel_whole_project"))
        self.project_check.stateChanged.connect(self.refresh)
        self.severity_filter = QComboBox()
        self.severity_filter.addItem(word.get("problems_panel_all_severities"), ALL_SEVERITIES)
        for severity, name_key in _SEVERITY_NAME_KEYS.items():
            self.severity_filter.addItem(word.get(name_key), int(severity))
        self.severity_filter.currentIndexChanged.connect(self._render_items)
        self.source_filter = QComboBox()
        self.source_filter.addItem(word.get("problems_panel_all_sources"), ALL_SOURCES)
        self.source_filter.currentIndexChanged.connect(self._render_items)
        self.fix_button = QPushButton(word.get("problems_panel_fix"))
        self.fix_button.clicked.connect(self.apply_available_fixes)
        self.status_label = QLabel(word.get("problems_panel_ready"))

        self.result_tree = QTreeWidget()
        self.result_tree.setColumnCount(len(_COLUMN_TITLE_KEYS))
        self.result_tree.setHeaderLabels([word.get(key) for key in _COLUMN_TITLE_KEYS])
        self.result_tree.setColumnWidth(COLUMN_MESSAGE, MESSAGE_COLUMN_WIDTH)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemDoubleClicked.connect(self._open_item)

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.project_check)
        controls.addWidget(self.severity_filter)
        controls.addWidget(self.source_filter)
        controls.addWidget(self.fix_button)
        controls.addWidget(self.status_label)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.result_tree)
        self.setLayout(layout)

        self.refresh()

    def diagnostics(self) -> list[Diagnostic]:
        """取得面板持有的所有診斷，不管篩選條件 / Every diagnostic held, whatever the filters say."""
        return self._store.select()

    def set_diagnostics(self, diagnostics: list, source: str = RUFF_SOURCE) -> None:
        """
        換掉面板持有的診斷並重畫清單
        Replace what the panel holds and redraw the list.

        :param diagnostics: 新的診斷，統一模型或舊形式都可以 / the diagnostics, in
            the unified model or the older shape
        :param source: 舊形式的診斷是誰報的 / who reported the older-shape ones
        """
        reports: dict[tuple[str, str], list[Diagnostic]] = {}
        for item in unify(diagnostics, source):
            reports.setdefault((item.source, item.uri), []).append(item)
        self._store.clear()
        for (item_source, uri), items in reports.items():
            self._store.publish(item_source, uri, items)
        self._render_items()

    def retranslate(self) -> None:
        """
        換語言後重新標示自己
        Relabel after the language changes.

        面板記著目前的診斷，因此不能整個拆掉重建；改字之後重畫清單，狀態列的文字
        也會跟著換成新語言。
        The panel is holding the current diagnostics and so cannot be rebuilt from
        scratch; relabelling and then redrawing the list also moves the status
        text to the new language.
        """
        word = language_wrapper.language_word_dict
        self.refresh_button.setText(word.get("problems_panel_refresh"))
        self.project_check.setText(word.get("problems_panel_whole_project"))
        self.fix_button.setText(word.get("problems_panel_fix"))
        self.severity_filter.setItemText(0, word.get("problems_panel_all_severities"))
        for severity, name_key in _SEVERITY_NAME_KEYS.items():
            self.severity_filter.setItemText(
                self.severity_filter.findData(int(severity)), word.get(name_key))
        self.source_filter.setItemText(0, word.get("problems_panel_all_sources"))
        self.result_tree.setHeaderLabels([word.get(key) for key in _COLUMN_TITLE_KEYS])
        self._render_items()

    def refresh(self) -> None:
        """
        重新讀取診斷並重畫清單
        Re-read the diagnostics and rebuild the list.

        單一檔案的診斷是編輯器持續在背景產生的，這裡只是取用最新結果；整個專案的
        檢查則要另外啟動，結果會晚一點才到。
        A single file's diagnostics are produced in the background by the editor,
        so those are just picked up; a project-wide check has to be started here
        and its result arrives later.
        """
        if self.project_check.isChecked():
            self.start_project_check()
            return
        self._stop_project_check()
        code_edit = current_code_editor(self._main_window)
        if code_edit is None:
            self.set_diagnostics([])
            return
        code_edit.request_lint()
        self.set_diagnostics(code_edit.lint_manager.diagnostics())

    def start_project_check(self) -> bool:
        """
        在背景檢查整個專案
        Start a project-wide check on a worker thread.

        ruff 走遍整個專案要好幾秒，在 UI 執行緒做會讓視窗整段時間沒有反應。
        Walking a whole project with ruff takes seconds, and doing it on the UI
        thread would leave the window unresponsive for all of it.

        :return: 是否啟動了檢查 / whether a check was started
        """
        self._stop_project_check()
        worker = ProjectLintWorker(self._project_root(), self)
        self._project_worker = worker
        worker.linted.connect(self._on_project_linted)
        # 先放掉參考再刪除，避免之後對已刪除的物件呼叫方法
        # Drop the reference before deleting, so nothing calls a deleted object
        worker.finished.connect(self._on_worker_finished)
        worker.finished.connect(worker.deleteLater)
        self.status_label.setText(
            language_wrapper.language_word_dict.get("problems_panel_checking"))
        worker.start()
        return True

    def _on_project_linted(self, diagnostics: list) -> None:
        """
        套用背景檢查的結果
        Apply the diagnostics a background check produced.

        只接受目前這個 worker 的結果：換過設定或再按一次重新檢查都會讓舊結果過期。
        Only the current worker's result is accepted, since changing the scope or
        rechecking makes an in-flight run stale.
        """
        if self.sender() is not self._project_worker:
            return
        self.set_diagnostics(list(diagnostics))

    def _on_worker_finished(self) -> None:
        """檢查結束後放掉參考 / Let go of the worker once it has finished."""
        if self.sender() is self._project_worker:
            self._project_worker = None

    def _stop_project_check(self) -> None:
        """結束仍在執行的專案檢查 / Stop a project check that is still running."""
        worker, self._project_worker = self._project_worker, None
        if worker is None:
            return
        try:
            if worker.isRunning():
                worker.blockSignals(True)
                worker.wait()
        except RuntimeError:
            # 它已經跑完並被刪除了 / It already finished and was deleted
            return

    def closeEvent(self, event) -> None:
        """關閉前先收掉背景檢查 / Stop the background check before closing."""
        self._stop_project_check()
        super().closeEvent(event)

    def _project_root(self) -> str:
        """取得要檢查的專案根目錄 / The project root to check."""
        working_dir = getattr(self._main_window, "working_dir", None)
        if working_dir and Path(str(working_dir)).is_dir():
            return str(working_dir)
        return os.getcwd()

    def visible_diagnostics(self) -> list[Diagnostic]:
        """
        取得符合嚴重度與來源篩選的診斷
        The diagnostics matching the severity and source filters.

        :return: 要顯示的診斷，順序固定 / the diagnostics to show, in a fixed order
        """
        severity = self.severity_filter.currentData()
        source = self.source_filter.currentData()
        return self._store.select(
            None if severity in (None, ALL_SEVERITIES) else [Severity(severity)],
            None if source in (None, ALL_SOURCES) else [source],
        )

    def _refresh_source_choices(self) -> None:
        """
        讓來源選單跟著目前有診斷的來源走
        Keep the source choices in step with the sources that have findings.

        原本選著的來源還在就維持，不在了就退回「全部來源」。重建期間擋住訊號，
        否則每加一個項目都會再重畫一次清單。
        A source that was selected stays selected while it still exists, and
        falls back to every source once it is gone. Signals are blocked while
        rebuilding, or each added item would redraw the list again.
        """
        selected = self.source_filter.currentData()
        all_sources_label = self.source_filter.itemText(0)
        self.source_filter.blockSignals(True)
        try:
            self.source_filter.clear()
            self.source_filter.addItem(all_sources_label, ALL_SOURCES)
            for source in self._store.sources():
                self.source_filter.addItem(source, source)
            self.source_filter.setCurrentIndex(max(self.source_filter.findData(selected), 0))
        finally:
            self.source_filter.blockSignals(False)

    def apply_available_fixes(self) -> bool:
        """
        套用 ruff 能自動修正的部分，並重新檢查
        Apply the fixes ruff can make, then check again.

        修正會改寫磁碟上的檔案，因此完成後把目前分頁重新讀進來，畫面才不會停在
        舊內容上。
        Fixing rewrites the files on disk, so the current tab is reloaded
        afterwards rather than left showing the old content.

        :return: ruff 可用並已執行時為 ``True`` / ``True`` when ruff ran
        """
        target = self._project_root() if self.project_check.isChecked() else self._current_file()
        if target is None:
            return False
        if not apply_fixes(target):
            return False
        self._reload_current_tab()
        self.refresh()
        return True

    def _current_file(self) -> str | None:
        """目前分頁的檔案 / The current tab's file."""
        code_edit = current_code_editor(self._main_window)
        path = getattr(code_edit, "current_file", None) if code_edit is not None else None
        return str(path) if path else None

    def _reload_current_tab(self) -> None:
        """把目前分頁的內容重新讀進來 / Re-read the current tab's file from disk."""
        code_edit = current_code_editor(self._main_window)
        path = self._current_file()
        if code_edit is None or path is None:
            return
        result = read_file_with_encoding(path)
        if result is not None:
            code_edit.setPlainText(result[1])

    def _render_items(self) -> None:
        """依目前診斷與篩選條件重建清單 / Rebuild the tree for the current filter."""
        word = language_wrapper.language_word_dict
        self._refresh_source_choices()
        visible = self.visible_diagnostics()
        self.result_tree.clear()
        for diagnostic in visible:
            file_path = to_path(diagnostic.uri)
            row = QTreeWidgetItem([
                diagnostic.code, diagnostic.message, str(diagnostic.range.start.line),
                Path(file_path).name if file_path else "",
                word.get(_SEVERITY_NAME_KEYS[diagnostic.severity]), diagnostic.source])
            row.setData(COLUMN_CODE, Qt.ItemDataRole.UserRole, diagnostic)
            self.result_tree.addTopLevelItem(row)
        if visible:
            self.status_label.setText(
                word.get("problems_panel_found").format(count=len(visible)))
        else:
            self.status_label.setText(word.get("problems_panel_clean"))

    def _open_item(self, row: QTreeWidgetItem, _column: int) -> None:
        """跳到被雙擊的診斷所在行 / Jump to the double-clicked diagnostic's line."""
        diagnostic = row.data(COLUMN_CODE, Qt.ItemDataRole.UserRole)
        if diagnostic is None:
            return
        self.jump_to_diagnostic(diagnostic)

    def jump_to_diagnostic(self, diagnostic) -> bool:
        """
        跳到診斷所在的位置，必要時先開啟該檔案
        Jump to a diagnostic, opening its file first when it is another one.

        :param diagnostic: 目標診斷，統一模型或舊形式都可以 / the diagnostic to
            jump to, in the unified model or the older shape
        :return: 成功跳轉時為 ``True`` / ``True`` when the caret moved
        """
        target = unify([diagnostic], RUFF_SOURCE)[0]
        file_path = to_path(target.uri)
        if (file_path and not self._is_current_file(target.uri)
                and hasattr(self._main_window, "go_to_new_tab")):
            self._main_window.go_to_new_tab(Path(file_path))
        code_edit = current_code_editor(self._main_window)
        if code_edit is None:
            return False
        return code_edit.jump_to_line(target.range.start.line)

    def _is_current_file(self, uri: str) -> bool:
        """
        判斷某個資源是不是目前分頁的檔案
        Whether a resource is the file in the current tab.

        目前分頁自己的診斷不必再「開啟」一次：同一個檔案換一種寫法去開，會被當成
        另一個檔案而多開一個分頁。
        The current tab's own diagnostics need no opening: asking to open the
        same file under another spelling would be taken for another file and
        open a second tab.
        """
        current = self._current_file()
        return current is not None and uri_key(to_uri(current)) == uri_key(uri)

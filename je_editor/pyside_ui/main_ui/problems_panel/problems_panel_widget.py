"""
問題面板：列出目前分頁的 lint 診斷
Problems panel: list the lint diagnostics of the current tab.

診斷是由編輯器在背景檢查後持有的，面板只負責顯示與跳轉，不自己執行 linter。
The editor already holds the diagnostics from its background check; the panel
only displays them and jumps to a line, never running the linter itself.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.utils.lint.ruff_diagnostics import Diagnostic
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 樹狀清單欄位索引 / Column indexes in the tree
COLUMN_CODE = 0
COLUMN_MESSAGE = 1
COLUMN_LINE = 2
# 訊息欄的預設寬度 / Default width of the message column
MESSAGE_COLUMN_WIDTH = 460


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
        self._diagnostics: list[Diagnostic] = []

        self.refresh_button = QPushButton(word.get("problems_panel_refresh"))
        self.refresh_button.clicked.connect(self.refresh)
        self.status_label = QLabel(word.get("problems_panel_ready"))

        self.result_tree = QTreeWidget()
        self.result_tree.setColumnCount(3)
        self.result_tree.setHeaderLabels([
            word.get("problems_panel_col_code"),
            word.get("problems_panel_col_message"),
            word.get("problems_panel_col_line"),
        ])
        self.result_tree.setColumnWidth(COLUMN_MESSAGE, MESSAGE_COLUMN_WIDTH)
        self.result_tree.setRootIsDecorated(False)
        self.result_tree.itemDoubleClicked.connect(self._open_item)

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.status_label)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.result_tree)
        self.setLayout(layout)

        self.refresh()

    def diagnostics(self) -> list[Diagnostic]:
        """取得面板目前顯示的診斷 / The diagnostics currently listed."""
        return list(self._diagnostics)

    def refresh(self) -> None:
        """
        重新讀取目前分頁的診斷並重畫清單
        Re-read the current tab's diagnostics and rebuild the list.

        編輯器持續在背景檢查，所以這裡只是取用最新結果。
        The editor keeps checking in the background, so this only picks up its
        latest result.
        """
        code_edit = current_code_editor(self._main_window)
        if code_edit is None:
            self._diagnostics = []
        else:
            code_edit.request_lint()
            self._diagnostics = code_edit.lint_manager.diagnostics()
        self._render_items()

    def _render_items(self) -> None:
        """依目前診斷重建清單 / Rebuild the tree from the current diagnostics."""
        word = language_wrapper.language_word_dict
        self.result_tree.clear()
        for diagnostic in self._diagnostics:
            row = QTreeWidgetItem([
                diagnostic.code, diagnostic.message, str(diagnostic.line)])
            row.setData(COLUMN_CODE, Qt.ItemDataRole.UserRole, diagnostic)
            self.result_tree.addTopLevelItem(row)
        if self._diagnostics:
            self.status_label.setText(
                word.get("problems_panel_found").format(count=len(self._diagnostics)))
        else:
            self.status_label.setText(word.get("problems_panel_clean"))

    def _open_item(self, row: QTreeWidgetItem, _column: int) -> None:
        """跳到被雙擊的診斷所在行 / Jump to the double-clicked diagnostic's line."""
        diagnostic = row.data(COLUMN_CODE, Qt.ItemDataRole.UserRole)
        if diagnostic is None:
            return
        self.jump_to_diagnostic(diagnostic)

    def jump_to_diagnostic(self, diagnostic: Diagnostic) -> bool:
        """
        把目前分頁的游標移到診斷所在行
        Move the current tab's caret to a diagnostic's line.

        :param diagnostic: 目標診斷 / the diagnostic to jump to
        :return: 成功跳轉時為 ``True`` / ``True`` when the caret moved
        """
        code_edit = current_code_editor(self._main_window)
        if code_edit is None:
            return False
        return code_edit.jump_to_line(diagnostic.line)

"""
大綱面板：顯示目前檔案的類別、函式與變數結構
Outline panel: show the class / function / variable structure of the current file.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.symbols.outline_tree import OutlineNode, build_outline_tree
from je_editor.utils.symbols.python_symbols import (
    SymbolInfo, extract_python_symbols, symbols_from_server
)

# 樹狀項目中儲存符號行號的資料角色 / Item data role holding a symbol's line number
_LINE_ROLE = Qt.ItemDataRole.UserRole


class OutlinePanelWidget(QWidget):
    """
    大綱面板
    The outline panel.

    重新整理時解析目前分頁的 Python 檔案並建立符號樹，雙擊項目可跳到定義處。
    Refreshing parses the current tab's Python file into a symbol tree; double-click
    jumps to the definition.
    """

    def __init__(self, main_window=None) -> None:
        """
        :param main_window: 用來找到目前編輯器的主視窗 / The window used to find the editor
        """
        super().__init__()
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        # 目前正在聽哪個編輯器的語言伺服器 / Whose language server is being listened to
        self._connected_client = None

        self.refresh_button = QPushButton(word.get("outline_panel_refresh"))
        self.refresh_button.clicked.connect(self.refresh)

        self.status_label = QLabel(word.get("outline_panel_ready"))

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            word.get("outline_panel_col_symbol"),
            word.get("outline_panel_col_kind"),
            word.get("outline_panel_col_line"),
        ])
        self.tree.itemDoubleClicked.connect(self._on_item_activated)
        self.tree.itemActivated.connect(self._on_item_activated)

        controls = QHBoxLayout()
        controls.addWidget(self.refresh_button)
        controls.addWidget(self.status_label)
        controls.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.tree)
        self.setLayout(layout)

        self.refresh()

    def retranslate(self) -> None:
        """
        換語言後重新標示自己
        Relabel after the language changes.
        """
        word = language_wrapper.language_word_dict
        self.refresh_button.setText(word.get("outline_panel_refresh"))
        self.tree.setHeaderLabels([
            word.get("outline_panel_col_symbol"),
            word.get("outline_panel_col_kind"),
            word.get("outline_panel_col_line"),
        ])
        self.refresh()

    def current_code_edit(self):
        """
        取得目前分頁的程式碼編輯器
        Return the code editor of the current tab, or ``None``.
        """
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        tab_widget = getattr(self._main_window, "tab_widget", None)
        if tab_widget is None:
            return None
        widget = tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            return widget.code_edit
        return None

    def refresh(self) -> None:
        """
        重新解析目前檔案並重建大綱
        Re-parse the current file and rebuild the outline.
        """
        code_edit = self.current_code_edit()
        self.tree.clear()
        if code_edit is None:
            self.status_label.setText(
                language_wrapper.language_word_dict.get("outline_panel_no_editor"))
            return
        symbols = extract_python_symbols(code_edit.toPlainText())
        if not symbols and self._ask_the_language_server(code_edit):
            return
        self._show_symbols(symbols)

    def _show_symbols(self, symbols: list[SymbolInfo]) -> None:
        """把符號畫成大綱 / Draw the symbols as an outline."""
        self.tree.clear()
        for node in build_outline_tree(symbols):
            self.tree.addTopLevelItem(self._build_item(node))
        self.tree.expandAll()
        jeditor_logger.info(f"outline_panel_widget.py built outline of {len(symbols)} symbols")
        self.status_label.setText(
            language_wrapper.language_word_dict.get("outline_panel_found").format(count=len(symbols)))

    def _ask_the_language_server(self, code_edit) -> bool:
        """
        向語言伺服器要這個檔案的符號
        Ask the language server for this file's symbols.

        大綱原本只靠 ``ast`` 解析 Python，其他語言一律是空的。有語言伺服器的話它
        知道同一件事，問它就好。
        The outline only ever parsed Python with ``ast``, leaving every other
        language empty. A language server knows the same thing, so it is asked.

        :param code_edit: 目前的編輯器 / the current editor
        :return: 有送出請求時為 ``True`` / ``True`` when a request was sent
        """
        client = getattr(code_edit, "lsp_client", None)
        if client is None or not client.running:
            return False
        if client is not self._connected_client:
            self._disconnect_client()
            client.symbols_ready.connect(self._on_server_symbols)
            self._connected_client = client
        if not code_edit.request_document_symbols():
            return False
        self.status_label.setText(
            language_wrapper.language_word_dict.get("outline_panel_ready"))
        return True

    def _disconnect_client(self) -> None:
        """不再聽上一個編輯器的回覆 / Stop listening to the previous editor's replies."""
        client, self._connected_client = self._connected_client, None
        if client is None:
            return
        try:
            client.symbols_ready.disconnect(self._on_server_symbols)
        except (RuntimeError, TypeError):
            # 它已經跟著分頁一起消失了 / It went away with its tab
            return

    def _on_server_symbols(self, symbols: list) -> None:
        """
        把語言伺服器回報的符號畫成大綱
        Draw the symbols a language server reported.

        :param symbols: ``{"name", "kind", "line", "depth"}`` 的清單 / the symbols
        """
        self._show_symbols(symbols_from_server(symbols))

    def _build_item(self, node: OutlineNode) -> QTreeWidgetItem:
        """把大綱節點轉成樹狀項目 / Turn an outline node into a tree item."""
        symbol = node.symbol
        item = QTreeWidgetItem([symbol.name, symbol.kind, str(symbol.line)])
        item.setData(0, _LINE_ROLE, symbol.line)
        for child in node.children:
            item.addChild(self._build_item(child))
        return item

    def _on_item_activated(self, item: QTreeWidgetItem, _column: int = 0) -> None:
        """雙擊項目時跳到符號所在行 / Jump to the symbol line on activation."""
        line = item.data(0, _LINE_ROLE)
        if line is None:
            return
        self.jump_to_symbol_line(int(line))

    def jump_to_symbol_line(self, line: int) -> bool:
        """
        在目前編輯器跳到指定的符號行
        Jump to a symbol line in the current editor.

        :param line: 1 起算的行號 / The 1-based line number
        :return: 成功跳轉時為 ``True`` / ``True`` when the jump happened
        """
        code_edit = self.current_code_edit()
        if code_edit is None or not hasattr(code_edit, "jump_to_line"):
            return False
        return code_edit.jump_to_line(line)


def build_symbol_items(symbols: list[SymbolInfo]) -> list[QTreeWidgetItem]:
    """
    把符號清單建成樹狀項目（供測試與重用）
    Build tree items from a symbol list (for reuse and testing).

    :param symbols: 要顯示的符號 / The symbols to display
    :return: 根層級的樹狀項目 / The top-level tree items
    """
    def _to_item(node: OutlineNode) -> QTreeWidgetItem:
        symbol = node.symbol
        item = QTreeWidgetItem([symbol.name, symbol.kind, str(symbol.line)])
        item.setData(0, _LINE_ROLE, symbol.line)
        for child in node.children:
            item.addChild(_to_item(child))
        return item

    return [_to_item(node) for node in build_outline_tree(symbols)]

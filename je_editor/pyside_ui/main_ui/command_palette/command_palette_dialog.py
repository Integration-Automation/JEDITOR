"""
指令面板：以模糊搜尋找到並執行任何選單指令
Command palette: fuzzy-search and run any menu command.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout, QWidget
)

from je_editor.pyside_ui.main_ui.command_palette.menu_command_collector import (
    collect_menu_commands
)
from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry, rank_commands
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 對話框尺寸 / Dialog size
DIALOG_WIDTH = 640
DIALOG_HEIGHT = 420
# 清單顯示筆數上限 / Maximum rows rendered in the result list
RESULT_LIMIT = 60
# 對話框相對於父視窗頂端的偏移 / Vertical offset from the parent window top
TOP_OFFSET = 120


class CommandPaletteDialog(QDialog):
    """
    指令面板對話框
    The command palette dialog.

    輸入文字即時過濾指令，Enter 執行選取的指令，Esc 關閉。
    Typing filters commands live, Enter runs the selected one, Esc closes.
    """

    def __init__(
            self, parent: QWidget, commands: list[CommandEntry],
            title: str | None = None, placeholder: str | None = None) -> None:
        """
        :param parent: 父視窗 / The parent window
        :param commands: 可執行的指令清單 / The runnable commands
        :param title: 視窗標題，``None`` 時使用指令面板的預設標題
            / Window title; ``None`` uses the command palette default
        :param placeholder: 輸入框提示文字，``None`` 時使用預設提示
            / Search box hint; ``None`` uses the default
        """
        super().__init__(parent)
        self._commands = commands
        self._visible_commands: list[CommandEntry] = []

        self.setWindowTitle(
            title or language_wrapper.language_word_dict.get("command_palette_title"))
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setModal(True)
        self.resize(DIALOG_WIDTH, DIALOG_HEIGHT)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(
            placeholder or language_wrapper.language_word_dict.get(
                "command_palette_placeholder"))
        self.search_input.textChanged.connect(self._refresh_results)
        self.search_input.installEventFilter(self)

        self.result_list = QListWidget(self)
        self.result_list.itemActivated.connect(self._run_item)
        self.result_list.itemDoubleClicked.connect(self._run_item)

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_input)
        layout.addWidget(self.result_list)
        self.setLayout(layout)

        self._refresh_results("")
        self.search_input.setFocus()

    def eventFilter(self, watched, event) -> bool:
        """
        讓上下鍵在輸入框中也能移動清單選取
        Route arrow keys from the search box to the result list.
        """
        if watched is self.search_input and isinstance(event, QKeyEvent) \
                and event.type() == QKeyEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                self._move_selection(1 if event.key() == Qt.Key.Key_Down else -1)
                return True
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self._run_current()
                return True
        return super().eventFilter(watched, event)

    def set_commands(self, commands: list[CommandEntry]) -> None:
        """
        替換候選清單並重新套用目前的查詢字串
        Replace the candidate list and re-apply the current query.

        供背景索引完成後把結果送進已開啟的面板。
        Lets a background indexer feed results into an already open picker.

        :param commands: 新的候選清單 / The new candidate list
        """
        self._commands = commands
        self._refresh_results(self.search_input.text())

    def _move_selection(self, step: int) -> None:
        """移動清單選取位置 / Move the selection within the result list."""
        count = self.result_list.count()
        if count == 0:
            return
        row = (self.result_list.currentRow() + step) % count
        self.result_list.setCurrentRow(row)

    def _refresh_results(self, query: str) -> None:
        """依查詢字串重新產生清單 / Rebuild the result list for the query."""
        self._visible_commands = rank_commands(query, self._commands, RESULT_LIMIT)
        self.result_list.clear()
        for command in self._visible_commands:
            label = command.path or command.title
            if command.shortcut:
                label = f"{label}\t({command.shortcut})"
            self.result_list.addItem(QListWidgetItem(label))
        if self.result_list.count() > 0:
            self.result_list.setCurrentRow(0)

    def _run_item(self, item: QListWidgetItem) -> None:
        """執行清單項目對應的指令 / Run the command behind a list row."""
        self._run_command_at(self.result_list.row(item))

    def _run_current(self) -> None:
        """執行目前選取的指令 / Run the currently selected command."""
        self._run_command_at(self.result_list.currentRow())

    def _run_command_at(self, row: int) -> None:
        """
        關閉面板後再觸發指令
        Close the palette first, then trigger the command.

        先關閉面板，指令自己彈出的對話框才不會被這個 modal 面板擋住。
        Closing first keeps a dialog opened by the command from being blocked
        by this modal palette.
        """
        if row < 0 or row >= len(self._visible_commands):
            return
        command = self._visible_commands[row]
        runner = _payload_runner(command.payload)
        jeditor_logger.info(f"command_palette_dialog.py run command: {command.path}")
        self.accept()
        if runner is not None:
            QTimer.singleShot(0, runner)


def _payload_runner(payload) -> object | None:
    """
    把項目的 payload 轉成可呼叫的觸發函式
    Turn an entry payload into a callable trigger.

    支援 ``QAction``（選單指令）與一般的可呼叫物件（例如開檔函式）。
    Supports a ``QAction`` (menu command) and any plain callable (e.g. an opener).

    :param payload: 項目攜帶的物件 / The object carried by the entry
    :return: 可呼叫的觸發函式，無法觸發時回傳 ``None``
        / A callable trigger, or ``None`` when the payload cannot be run
    """
    if payload is None:
        return None
    if callable(payload):
        return payload
    trigger = getattr(payload, "trigger", None)
    return trigger if callable(trigger) else None


def open_command_palette(main_window: EditorMain) -> CommandPaletteDialog | None:
    """
    建立並顯示指令面板
    Build and show the command palette.

    :param main_window: 主編輯器視窗 / The main editor window
    :return: 已顯示的對話框，沒有任何指令時回傳 ``None``
        / The shown dialog, or ``None`` when no command was collected
    """
    jeditor_logger.info("command_palette_dialog.py open_command_palette")
    commands = collect_menu_commands(getattr(main_window, "menu", None))
    if not commands:
        return None
    dialog = CommandPaletteDialog(main_window, commands)
    dialog.show()
    return dialog

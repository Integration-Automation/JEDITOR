"""
編輯快捷鍵的對話框
A dialog for changing the keyboard shortcuts.

快捷鍵原本散落在各個選單與編輯器裡各自寫死，衝突只能等到按下去沒反應才發現。
現在全部集中在一份表裡，這個對話框就是那份表的編輯介面：改完立刻檢查有沒有兩個
指令搶同一組按鍵，存檔後新開的分頁就照新設定走。
The shortcuts used to be written down separately in each menu and in the editor,
so a clash only showed up as a key that did nothing. They now live in one table,
and this is its editor: a change is checked for two commands claiming the same
keys, and a save applies to newly opened tabs.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QKeySequenceEdit, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget
)

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.shortcuts.shortcut_registry import (
    DEFAULT_SHORTCUTS, EDITOR_SHORTCUTS, clean_overrides, effective_shortcuts,
    find_conflicts
)

# 樹狀清單的欄位 / The columns in the tree
COLUMN_COMMAND = 0
COLUMN_SEQUENCE = 1
# 指令欄的預設寬度 / Default width of the command column
COMMAND_COLUMN_WIDTH = 260


def command_label(command: str) -> str:
    """
    取得指令的顯示名稱
    The name a command is shown under.

    有翻譯就用翻譯，沒有的話把指令名稱本身整理成看得懂的樣子，這樣新增指令時不會
    因為忘了加翻譯就變成一列空白。
    A translation is used when there is one, and otherwise the command's own name
    is tidied into something readable, so a newly added command never shows up as
    an empty row because its translation was forgotten.

    :param command: 指令名稱 / the command's name
    :return: 顯示名稱 / the label to show
    """
    translated = language_wrapper.language_word_dict.get(f"shortcut_{command}")
    return translated or command.replace("_", " ").capitalize()


class ShortcutSettingsDialog(QDialog):
    """
    列出所有指令並讓使用者改按鍵
    List every command and let the user change its keys.
    """

    def __init__(self, main_window=None, parent: QWidget | None = None) -> None:
        """
        :param main_window: 儲存後要通知的主視窗 / the window told about a save
        :param parent: Qt 父元件 / the Qt parent
        """
        super().__init__(parent)
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        self.setWindowTitle(word.get("shortcut_settings_title"))
        self._editors: dict[str, QKeySequenceEdit] = {}

        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels([
            word.get("shortcut_settings_col_command"),
            word.get("shortcut_settings_col_keys"),
        ])
        self.tree.setColumnWidth(COLUMN_COMMAND, COMMAND_COLUMN_WIDTH)
        self.tree.setRootIsDecorated(False)

        self.status_label = QLabel("")
        self.save_button = QPushButton(word.get("shortcut_settings_save"))
        self.save_button.clicked.connect(self.save)
        self.reset_button = QPushButton(word.get("shortcut_settings_reset"))
        self.reset_button.clicked.connect(self.reset_to_defaults)

        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.reset_button)
        buttons.addWidget(self.status_label)
        buttons.addStretch()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(word.get("shortcut_settings_hint")))
        layout.addWidget(self.tree)
        layout.addLayout(buttons)
        self.setLayout(layout)

        self._fill(effective_shortcuts(user_setting_dict.get("shortcuts")))

    def _fill(self, shortcuts: dict[str, str]) -> None:
        """依目前的設定重建清單 / Rebuild the list from the given shortcuts."""
        self.tree.clear()
        self._editors = {}
        # 編輯器的指令排在後面，選單與工具列在前，與使用者尋找的順序一致
        # Menu and toolbar commands come first and the editor's after, which is
        # the order someone looks for them in
        for command in sorted(DEFAULT_SHORTCUTS, key=lambda name: (name in EDITOR_SHORTCUTS, name)):
            row = QTreeWidgetItem([command_label(command), ""])
            row.setData(COLUMN_COMMAND, Qt.ItemDataRole.UserRole, command)
            self.tree.addTopLevelItem(row)
            editor = QKeySequenceEdit(QKeySequence(shortcuts.get(command, "")))
            editor.keySequenceChanged.connect(self._check_conflicts)
            self.tree.setItemWidget(row, COLUMN_SEQUENCE, editor)
            self._editors[command] = editor
        self._check_conflicts()

    def current_shortcuts(self) -> dict[str, str]:
        """
        取得畫面上目前的按鍵設定
        The shortcuts as the dialog currently shows them.

        :return: 指令對應按鍵 / command mapped to sequence
        """
        return {
            command: editor.keySequence().toString()
            for command, editor in self._editors.items()
        }

    def conflicts(self) -> list[tuple[str, list[str]]]:
        """
        取得目前設定中重複的按鍵
        The sequences currently claimed by more than one command.

        :return: ``(按鍵, 指令清單)`` / ``(sequence, commands)``
        """
        return find_conflicts(self.current_shortcuts())

    def _check_conflicts(self) -> None:
        """把衝突狀況顯示出來 / Say whether anything currently clashes."""
        word = language_wrapper.language_word_dict
        clashes = self.conflicts()
        if not clashes:
            self.status_label.setText("")
            self.save_button.setEnabled(True)
            return
        sequence, commands = clashes[0]
        self.status_label.setText(word.get("shortcut_settings_conflict").format(
            keys=sequence, commands=", ".join(command_label(name) for name in commands)))
        # 有衝突就存不了：存下去等於讓兩個功能一起失效
        # A clash cannot be saved: doing so would disable both features at once
        self.save_button.setEnabled(False)

    def reset_to_defaults(self) -> None:
        """把所有按鍵改回預設值 / Put every shortcut back to its default."""
        self._fill(dict(DEFAULT_SHORTCUTS))

    def save(self) -> bool:
        """
        儲存設定
        Store the shortcuts.

        只記下與預設不同的項目，設定檔因此不會被幾十個沒改過的值塞滿，日後改動預設
        值時使用者也能跟著更新。
        Only what differs from a default is recorded, so the settings file does not
        fill with dozens of untouched values and a later change to a default still
        reaches the user.

        :return: 有存起來時為 ``True``；有衝突時為 ``False``
            ``True`` when stored, and ``False`` while something clashes
        """
        if self.conflicts():
            return False
        user_setting_dict["shortcuts"] = clean_overrides(self.current_shortcuts())
        notify = getattr(self._main_window, "reload_shortcuts", None)
        if callable(notify):
            notify()
        self.accept()
        return True

"""
編輯使用者片段的對話框
A dialog for editing the user's snippets.

先前只能手動改 ``snippets.json``；這裡讓新增、修改與刪除都在編輯器裡完成，存檔
後立刻對開著的分頁生效。
Editing ``snippets.json`` by hand used to be the only way. This adds, changes and
removes them inside the editor, and saving takes effect in the open tabs at once.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QPushButton,
    QVBoxLayout, QWidget
)

from je_editor.pyside_ui.code.snippets.snippet_manager import load_snippets, save_snippets
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 新片段的預設觸發字 / The trigger a new snippet starts with
NEW_TRIGGER = "new"


class SnippetEditorDialog(QDialog):
    """
    列出片段並讓使用者編輯
    List the snippets and let the user edit them.
    """

    def __init__(self, main_window=None, parent: QWidget | None = None) -> None:
        """
        :param main_window: 儲存後要通知的主視窗 / the window told about a save
        :param parent: Qt 父元件 / the Qt parent
        """
        super().__init__(parent)
        word = language_wrapper.language_word_dict
        self._main_window = main_window
        self.setWindowTitle(word.get("snippet_editor_title"))
        self._snippets = load_snippets()

        self.trigger_list = QListWidget()
        self.trigger_list.addItems(sorted(self._snippets))
        self.trigger_list.currentTextChanged.connect(self._show_body)

        self.body_edit = QPlainTextEdit()
        self.body_edit.setPlaceholderText(word.get("snippet_editor_body_placeholder"))

        self.add_button = QPushButton(word.get("snippet_editor_add"))
        self.add_button.clicked.connect(self.add_snippet)
        self.remove_button = QPushButton(word.get("snippet_editor_remove"))
        self.remove_button.clicked.connect(self.remove_snippet)
        self.save_button = QPushButton(word.get("snippet_editor_save"))
        self.save_button.clicked.connect(self.save)

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(word.get("snippet_editor_hint")))
        body_row = QHBoxLayout()
        body_row.addWidget(self.trigger_list, 1)
        body_row.addWidget(self.body_edit, 2)
        layout.addLayout(body_row)
        layout.addLayout(buttons)
        self.setLayout(layout)
        if self.trigger_list.count():
            self.trigger_list.setCurrentRow(0)

    def snippets(self) -> dict[str, str]:
        """取得目前編輯中的片段 / The snippets as they stand in the dialog."""
        return dict(self._snippets)

    def _show_body(self, trigger: str) -> None:
        """切換到另一個片段時顯示它的內容 / Show a snippet's body when it is selected."""
        self._remember_body()
        self._current_trigger = trigger
        self.body_edit.setPlainText(self._snippets.get(trigger, ""))

    def _remember_body(self) -> None:
        """把編輯中的內容記回目前的片段 / Keep the edited body against its trigger."""
        trigger = getattr(self, "_current_trigger", "")
        if trigger:
            self._snippets[trigger] = self.body_edit.toPlainText()

    def add_snippet(self) -> str:
        """
        新增一個片段
        Add a snippet.

        觸發字重複時自動加上編號，因此新片段不會覆蓋既有的。
        A repeated trigger is numbered, so a new snippet never overwrites one
        that is already there.

        :return: 新片段的觸發字 / the new snippet's trigger
        """
        self._remember_body()
        trigger = NEW_TRIGGER
        index = 2
        while trigger in self._snippets:
            trigger = f"{NEW_TRIGGER}{index}"
            index += 1
        self._snippets[trigger] = "$0"
        self.trigger_list.addItem(trigger)
        self.trigger_list.setCurrentRow(self.trigger_list.count() - 1)
        return trigger

    def remove_snippet(self) -> bool:
        """
        刪除選取的片段
        Remove the selected snippet.

        :return: 有刪除時為 ``True`` / ``True`` when one was removed
        """
        row = self.trigger_list.currentRow()
        if row < 0:
            return False
        trigger = self.trigger_list.item(row).text()
        self._snippets.pop(trigger, None)
        self._current_trigger = ""
        self.trigger_list.takeItem(row)
        self.body_edit.setPlainText("")
        return True

    def save(self) -> bool:
        """
        儲存片段，並讓開著的分頁立刻套用
        Save the snippets and let the open tabs pick them up at once.

        :return: 儲存成功時為 ``True`` / ``True`` when they were saved
        """
        self._remember_body()
        if not save_snippets(self._snippets):
            return False
        self._reload_open_tabs()
        return True

    def _reload_open_tabs(self) -> None:
        """請每個編輯分頁重新載入片段 / Ask each editor tab to reload its snippets."""
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        tab_widget = getattr(self._main_window, "tab_widget", None)
        if tab_widget is None:
            return
        for index in range(tab_widget.count()):
            widget = tab_widget.widget(index)
            if isinstance(widget, EditorWidget):
                widget.code_edit.snippet_manager.reload()

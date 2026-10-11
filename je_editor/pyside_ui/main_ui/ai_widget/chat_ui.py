"""
AI 對話面板
The AI chat panel.

面板只認得「登記表裡的某個供應者」，不認得任何一家的 SDK：送出對話、邊收邊顯示、
取消與報錯對每個供應者都是同一段程式碼。
The panel knows a provider from the registry and nobody's SDK: sending a
conversation, showing the reply as it arrives, cancelling and reporting an error
are the same code for every provider.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QTextCursor
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit, QPushButton,
    QSizePolicy, QWidget
)

from je_editor.adapters.default_services import build_default_services, reload_ai_settings
from je_editor.core.ai.ai_provider import AIProvider, ChatResponse
from je_editor.core.ai.chat_session import ChatSession
from je_editor.core.services.editor_services import EditorServices
from je_editor.pyside_ui.dialog.ai_dialog.set_ai_dialog import SetAIDialog
from je_editor.pyside_ui.main_ui.ai_widget.chat_worker import ChatWorker
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 字型大小選單的範圍與預設值 / The range and the default of the font size list
_FONT_SIZE_MIN = 2
_FONT_SIZE_MAX = 100
_FONT_SIZE_STEP = 2
_DEFAULT_FONT_SIZE = 16
# 面板的欄數 / How many columns the panel's grid has
_GRID_COLUMNS = 4


def services_for(main_window: object) -> EditorServices:
    """
    取得視窗的核心服務；宿主視窗沒有的話就自己建一組
    The window's core services, or a set of its own when the host window has none.

    :param main_window: 開啟這個面板的視窗 / the window that opened this panel
    :return: 核心服務 / the core services
    """
    services = getattr(main_window, "services", None)
    return services if isinstance(services, EditorServices) else build_default_services()


class ChatUI(QWidget):
    """
    與 AI 助理對話的面板
    The panel for talking to the AI assistant.
    """

    def __init__(self, main_window: EditorMain | None = None) -> None:
        """
        :param main_window: 開啟這個面板的視窗 / the window that opened this panel
        """
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.main_window = main_window
        self._services = services_for(main_window)
        self._session = ChatSession()
        self._worker: ChatWorker | None = None
        self.set_ai_config_dialog: SetAIDialog | None = None
        self._build_widgets()
        self._lay_out()
        self.retranslate()
        self.refresh_providers()
        self._set_waiting(False)

    # ---- construction ----------------------------------------------------

    def _build_widgets(self) -> None:
        """建立面板上的元件並接好訊號 / Build the panel's widgets and connect their signals."""
        self.chat_panel = QPlainTextEdit()
        self.chat_panel.setReadOnly(True)
        self.chat_panel.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.prompt_input = QLineEdit()
        self.prompt_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.prompt_input.returnPressed.connect(self.call_ai_model)

        self.provider_label = QLabel()
        self.provider_combobox = QComboBox()
        self.provider_combobox.currentIndexChanged.connect(self._on_provider_changed)
        self.model_label = QLabel()
        self.model_combobox = QComboBox()
        self.model_combobox.setEditable(True)

        self.font_size_combobox = QComboBox()
        for font_size in range(_FONT_SIZE_MIN, _FONT_SIZE_MAX + 1, _FONT_SIZE_STEP):
            self.font_size_combobox.addItem(str(font_size))
        self.font_size_combobox.setCurrentText(str(_DEFAULT_FONT_SIZE))
        self.font_size_combobox.currentTextChanged.connect(self.update_panel_text_size)
        self.update_panel_text_size()

        self.call_ai_model_button = QPushButton()
        self.call_ai_model_button.clicked.connect(self.call_ai_model)
        self.stop_button = QPushButton()
        self.stop_button.clicked.connect(self.stop)
        self.new_chat_button = QPushButton()
        self.new_chat_button.clicked.connect(self.new_chat)
        self.set_ai_config_button = QPushButton()
        self.set_ai_config_button.clicked.connect(self.set_ai_config)
        self.load_ai_config_button = QPushButton()
        self.load_ai_config_button.clicked.connect(self._reload_from_file)
        self.status_label = QLabel()

    def _lay_out(self) -> None:
        """把元件排進格線 / Place the widgets in the grid."""
        self.grid_layout = QGridLayout()
        rows = (
            (self.provider_label, self.provider_combobox, self.model_label, self.model_combobox),
            (self.chat_panel,),
            (self.call_ai_model_button, self.stop_button, self.new_chat_button,
             self.font_size_combobox),
            (self.set_ai_config_button, self.load_ai_config_button, self.status_label),
            (self.prompt_input,),
        )
        for row, widgets in enumerate(rows):
            for column, widget in enumerate(widgets):
                # 一列裡最後一個元件佔滿剩下的欄 / The last widget of a row takes the columns left
                span = _GRID_COLUMNS - column if column == len(widgets) - 1 else 1
                self.grid_layout.addWidget(widget, row, column, 1, span)
        self.setLayout(self.grid_layout)

    def retranslate(self) -> None:
        """
        換語言後重新標示自己
        Relabel after the language changes.

        面板握著進行中的對話，所以不能整個拆掉重建。
        The panel holds the conversation in progress, so it cannot be rebuilt.
        """
        word = language_wrapper.language_word_dict
        self.provider_label.setText(word.get("chat_ui_provider_label"))
        self.model_label.setText(word.get("chat_ui_model_label"))
        self.call_ai_model_button.setText(word.get("chat_ui_call_ai_model_button"))
        self.stop_button.setText(word.get("chat_ui_stop_button"))
        self.new_chat_button.setText(word.get("chat_ui_new_chat_button"))
        self.set_ai_config_button.setText(word.get("chat_ui_set_ai_button"))
        self.load_ai_config_button.setText(word.get("chat_ui_load_ai_button"))
        if not self._session.is_waiting:
            self.status_label.setText(word.get("chat_ui_status_ready"))

    # ---- providers and settings ------------------------------------------

    def refresh_providers(self) -> None:
        """
        讓供應者選單跟著登記表與設定走
        Bring the provider list in step with the registry and the settings.
        """
        names = self._services.ai_providers.names()
        active = self._services.ai_settings.active_provider
        self.provider_combobox.blockSignals(True)
        try:
            self.provider_combobox.clear()
            self.provider_combobox.addItems(names)
            if active in names:
                self.provider_combobox.setCurrentText(active)
        finally:
            self.provider_combobox.blockSignals(False)
        self._refresh_models()

    def current_provider(self) -> AIProvider | None:
        """目前選用的供應者，沒有時為 ``None`` / The provider in use, or ``None``."""
        return self._services.ai_providers.get(self.provider_combobox.currentText())

    def _on_provider_changed(self) -> None:
        """換了供應者：記下選擇並換上它的模型 / A new provider was picked: note it and show its models."""
        self._services.ai_settings.active_provider = self.provider_combobox.currentText()
        self._refresh_models()

    def _refresh_models(self) -> None:
        """列出目前供應者的模型，並選上設定裡的那一個 / List the provider's models and pick the configured one."""
        provider = self.current_provider()
        offered = [model.model_id for model in provider.models()] if provider is not None else []
        configured = self._services.ai_settings.settings_for(
            self.provider_combobox.currentText()).model
        self.model_combobox.clear()
        self.model_combobox.addItems(offered)
        self.model_combobox.setCurrentText(configured or (offered[0] if offered else ""))

    def set_ai_config(self) -> None:
        """開啟 AI 設定對話框 / Open the AI settings dialog."""
        self.set_ai_config_dialog = SetAIDialog(self._services, self.provider_combobox.currentText())
        self.set_ai_config_dialog.settings_applied.connect(self.refresh_providers)
        self.set_ai_config_dialog.show()

    def _reload_from_file(self) -> None:
        """從設定檔重新載入，並告訴使用者載入完成 / Reload from the settings file and say so."""
        self.load_ai_config(show_load_complete=True)

    def load_ai_config(self, show_load_complete: bool = False) -> None:
        """
        從設定檔重新載入 AI 設定
        Load the AI settings from their file again.

        :param show_load_complete: 是否跳出「載入完成」的訊息 / whether to say that loading finished
        """
        reload_ai_settings(self._services)
        self.refresh_providers()
        if show_load_complete:
            word = language_wrapper.language_word_dict
            QMessageBox.information(
                self, word.get("load_ai_messagebox_title"), word.get("load_ai_messagebox_text"))

    # ---- conversation ----------------------------------------------------

    def update_panel_text_size(self) -> None:
        """套用選單選的字型大小 / Apply the font size picked in the list."""
        self.chat_panel.setFont(QFontDatabase.font(
            self.font().family(), "", int(self.font_size_combobox.currentText())))

    def call_ai_model(self) -> bool:
        """
        把輸入框的文字送給目前的供應者
        Send what is in the input box to the provider in use.

        :return: 是否真的送出了請求 / whether a request was actually sent
        """
        word = language_wrapper.language_word_dict
        provider = self.current_provider()
        if provider is None:
            QMessageBox.warning(
                self, word.get("call_ai_model_error_title"), word.get("chat_ui_no_provider"))
            return False
        settings = self._services.ai_settings.settings_for(provider.name)
        request = self._session.ask(
            self.prompt_input.text(), self.model_combobox.currentText().strip(),
            settings.system_prompt)
        if request is None:
            return False
        self._append_line(f"{word.get('chat_ui_you_prefix')}: {request.messages[-1].content}")
        self._append_line(f"{word.get('chat_ui_assistant_prefix')}: ")
        self.prompt_input.clear()
        worker = ChatWorker(provider, request)
        worker.text_ready.connect(self._on_text)
        worker.replied.connect(self._on_replied)
        worker.failed.connect(self._on_failed)
        self._worker = worker
        self._set_waiting(True)
        worker.start_request()
        return True

    def stop(self) -> None:
        """取消進行中的請求 / Cancel the request in flight."""
        if self._worker is not None:
            self._worker.cancel()

    def new_chat(self) -> None:
        """丟掉目前的對話，重新開始 / Drop the conversation and start again."""
        self.stop()
        self._worker = None
        self._session.clear()
        self.chat_panel.clear()
        self._set_waiting(False)

    def _on_text(self, piece: str) -> None:
        """把剛收到的一段回覆接在畫面最後 / Add a piece of the reply to the end of what is shown."""
        if self.sender() is not self._worker:
            return
        cursor = self.chat_panel.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(piece)
        self.chat_panel.setTextCursor(cursor)

    def _on_replied(self, response: ChatResponse) -> None:
        """回覆完成：記進對話並顯示用量 / The reply is complete: note it and show the usage."""
        if self.sender() is not self._worker:
            return
        word = language_wrapper.language_word_dict
        self._session.answered(response)
        self._worker = None
        self._append_line("")
        self._set_waiting(False)
        if response.cancelled:
            self.status_label.setText(word.get("chat_ui_status_cancelled"))
        elif response.input_tokens is None or response.output_tokens is None:
            self.status_label.setText(word.get("chat_ui_status_done"))
        else:
            self.status_label.setText(word.get("chat_ui_status_tokens").format(
                input=response.input_tokens, output=response.output_tokens))

    def _on_failed(self, message: str) -> None:
        """請求失敗：丟掉那一句並告訴使用者原因 / The request failed: drop the prompt and say why."""
        if self.sender() is not self._worker:
            return
        word = language_wrapper.language_word_dict
        self._session.failed()
        self._worker = None
        self._append_line("")
        self._set_waiting(False)
        self.status_label.setText(word.get("chat_ui_status_failed"))
        QMessageBox.warning(self, word.get("call_ai_model_error_title"), message)

    def _append_line(self, text: str) -> None:
        """在畫面最後另起一行 / Start a new line at the end of what is shown."""
        self.chat_panel.appendPlainText(text)

    def _set_waiting(self, waiting: bool) -> None:
        """依是否在等回覆切換按鈕與狀態文字 / Switch the buttons and the status for waiting or not."""
        self.call_ai_model_button.setEnabled(not waiting)
        self.prompt_input.setEnabled(not waiting)
        self.stop_button.setEnabled(waiting)
        word = language_wrapper.language_word_dict
        self.status_label.setText(
            word.get("chat_ui_status_waiting" if waiting else "chat_ui_status_ready"))

    def closeEvent(self, event) -> None:
        """關閉前取消還在進行的請求 / Cancel a request still in flight before closing."""
        self.stop()
        self._worker = None
        if self.set_ai_config_dialog is not None:
            self.set_ai_config_dialog.close()
        super().closeEvent(event)

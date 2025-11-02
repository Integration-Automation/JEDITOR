from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Union

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QScrollArea, QLabel, QComboBox, QGridLayout, QPushButton, \
    QMessageBox, QSizePolicy, QLineEdit

from je_editor.pyside_ui.dialog.ai_dialog.set_ai_dialog import SetAIDialog
from je_editor.pyside_ui.main_ui.ai_widget.ai_config import AIConfig, ai_config
from je_editor.pyside_ui.main_ui.ai_widget.ask_thread import AskThread
from je_editor.pyside_ui.main_ui.ai_widget.langchain_interface import LangChainInterface
from je_editor.utils.json.json_file import read_json
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


class ChatUI(QWidget):

    def __init__(self, main_window: EditorMain):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)  # 關閉視窗時自動釋放資源 / Auto delete on close
        self.main_window = main_window

        # ---------------- Chat Panel 聊天面板 ----------------
        self.chat_panel = QPlainTextEdit()  # 顯示聊天訊息的文字框 / Text area for chat messages
        self.chat_panel.setLineWrapMode(self.chat_panel.LineWrapMode.NoWrap)  # 不自動換行 / Disable line wrap
        self.chat_panel.setReadOnly(True)  # 設為唯讀，避免使用者直接輸入 / Read-only
        self.chat_panel_scroll_area = QScrollArea()  # 加入滾動區域 / Scroll area for chat panel
        self.chat_panel_scroll_area.setWidgetResizable(True)
        self.chat_panel_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.chat_panel_scroll_area.setWidget(self.chat_panel)
        self.chat_panel.setFont(QFontDatabase.font(self.font().family(), "", 16))  # 設定字體大小 / Set font size

        # ---------------- Prompt Input 輸入框 ----------------
        self.prompt_input = QLineEdit()  # 使用者輸入提示詞 / Input field for prompts
        self.prompt_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.prompt_input.returnPressed.connect(self.call_ai_model)  # 按 Enter 時呼叫 AI / Call AI on Enter

        # ---------------- Font Size Combobox 字體大小選單 ----------------
        self.font_size_label = QLabel(language_wrapper.language_word_dict.get("font_size"))  # 標籤 / Label
        self.font_size_combobox = QComboBox()  # 下拉選單 / Dropdown for font size
        for font_size in range(2, 101, 2):  # 提供 2~100 的字體大小選項 / Font size options
            self.font_size_combobox.addItem(str(font_size))
        self.font_size_combobox.setCurrentText("16")  # 預設字體大小 / Default font size
        self.font_size_combobox.currentTextChanged.connect(self.update_panel_text_size)

        # ---------------- Buttons 按鈕 ----------------
        self.set_ai_config_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_set_ai_button"))
        self.set_ai_config_button.clicked.connect(self.set_ai_config)  # 開啟 AI 設定視窗 / Open AI config dialog

        self.load_ai_config_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_load_ai_button"))
        self.load_ai_config_button.clicked.connect(
            lambda: self.load_ai_config(show_load_complete=True))  # 載入設定 / Load config

        self.call_ai_model_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_call_ai_model_button"))
        self.call_ai_model_button.clicked.connect(self.call_ai_model)  # 呼叫 AI / Call AI

        # ---------------- Layout 版面配置 ----------------
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.chat_panel_scroll_area, 0, 0, 1, 4)  # 聊天面板 / Chat panel
        self.grid_layout.addWidget(self.call_ai_model_button, 1, 0)  # 呼叫 AI 按鈕 / Call AI button
        self.grid_layout.addWidget(self.font_size_combobox, 1, 1)  # 字體大小選單 / Font size combobox
        self.grid_layout.addWidget(self.set_ai_config_button, 1, 2)  # 設定 AI 按鈕 / Set AI config button
        self.grid_layout.addWidget(self.load_ai_config_button, 1, 3)  # 載入設定按鈕 / Load AI config button
        self.grid_layout.addWidget(self.prompt_input, 2, 0, 1, 4)  # 輸入框 / Prompt input

        # ---------------- Variables 變數 ----------------
        self.ai_config: AIConfig = ai_config  # AI 設定物件 / AI config object
        self.lang_chain_interface: Union[LangChainInterface, None] = None  # LangChain 介面 / LangChain interface
        self.set_ai_config_dialog = None  # 設定對話框 / Config dialog

        # ---------------- Timer 計時器 ----------------
        self.pull_message_timer = QTimer(self)  # 定時檢查訊息佇列 / Timer to pull messages
        self.pull_message_timer.setInterval(1000)  # 每秒檢查一次 / Check every 1 second
        self.pull_message_timer.timeout.connect(self.pull_message)
        self.pull_message_timer.start()

        # ---------------- Set Layout 設定版面 ----------------
        self.setLayout(self.grid_layout)

        # ---------------- Load AI Config 載入 AI 設定 ----------------
        self.load_ai_config()

    # 更新聊天面板字體大小 / Update chat panel font size
    def update_panel_text_size(self):
        self.chat_panel.setFont(
            QFontDatabase.font(self.font().family(), "", int(self.font_size_combobox.currentText())))

    # 載入 AI 設定檔 / Load AI configuration file
    def load_ai_config(self, show_load_complete: bool = False):
        ai_config_file = Path(str(Path.cwd()) + "/" + ".jeditor/ai_config.json")
        if ai_config_file.exists():
            with open(ai_config_file, "r", encoding="utf-8"):
                json_data: dict = read_json(str(ai_config_file))
            if json_data:
                # 確認 AI_model 設定存在且格式正確 / Ensure AI_model config exists and valid
                if json_data.get("AI_model") and len(json_data.get("AI_model")) == 4:
                    ai_info: dict = json_data.get("AI_model")
                    if ai_info.get("ai_base_url") and ai_info.get("chat_model"):
                        ai_config.choosable_ai.update(json_data)  # 更新全域設定 / Update global config
                    # 建立 LangChain 介面 / Initialize LangChain interface
                    self.lang_chain_interface = LangChainInterface(
                        main_window=self,
                        api_key=ai_info.get("ai_api_key"),
                        base_url=ai_info.get("ai_base_url"),
                        chat_model=ai_info.get("chat_model"),
                        prompt_template=ai_info.get("prompt_template"),
                    )
            if show_load_complete:
                load_complete = QMessageBox(self)
                load_complete.setWindowTitle(language_wrapper.language_word_dict.get("load_ai_messagebox_title"))
                load_complete.setText(language_wrapper.language_word_dict.get("load_ai_messagebox_text"))
                load_complete.exec()

    # 呼叫 AI 模型 / Call AI model
    def call_ai_model(self):
        if isinstance(self.lang_chain_interface, LangChainInterface):
            # 建立新執行緒處理 AI 請求 / Start a new thread for AI request
            thread = AskThread(lang_chain_interface=self.lang_chain_interface, prompt=self.prompt_input.text())
            thread.start()
        else:
            # 若未正確設定 AI，顯示錯誤訊息 / Show error if AI not configured
            ai_info = ai_config.choosable_ai.get('AI_model')
            QMessageBox.warning(self,
                                language_wrapper.language_word_dict.get("call_ai_model_error_title"),
                                language_wrapper.language_word_dict.get(
                                    f"ai_api_key: {ai_info.get('ai_api_key')}, \n"
                                    f"ai_base_url: {ai_info.get('ai_base_url')}, \n"
                                    f"chat_model: {ai_info.get('chat_model')}, \n"
                                    f"prompt_template: {ai_info.get('prompt_template')}"))

    # 從訊息佇列中取出 AI 回覆並顯示 / Pull AI response from queue
    def pull_message(self):
        if not ai_config.message_queue.empty():
            ai_response = ai_config.message_queue.get_nowait()
            self.chat_panel.appendPlainText(ai_response)  # 顯示回覆 / Display response
            self.chat_panel.appendPlainText("\n")

    # 開啟 AI 設定對話框 / Open AI config dialog
    def set_ai_config(self):
        self.set_ai_config_dialog = SetAIDialog()
        self.set_ai_config_dialog.show()

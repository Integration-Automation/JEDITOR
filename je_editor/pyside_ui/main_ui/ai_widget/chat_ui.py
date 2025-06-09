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
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.main_window = main_window
        # Chat panel
        self.chat_panel = QPlainTextEdit()
        self.chat_panel.setLineWrapMode(self.chat_panel.LineWrapMode.NoWrap)
        self.chat_panel.setReadOnly(True)
        self.chat_panel_scroll_area = QScrollArea()
        self.chat_panel_scroll_area.setWidgetResizable(True)
        self.chat_panel_scroll_area.setViewportMargins(0, 0, 0, 0)
        self.chat_panel_scroll_area.setWidget(self.chat_panel)
        self.chat_panel.setFont(QFontDatabase.font(self.font().family(), "", 16))
        # Prompt input
        self.prompt_input = QLineEdit()
        self.prompt_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.prompt_input.returnPressed.connect(self.call_ai_model)
        # Font size combobox
        self.font_size_label = QLabel(language_wrapper.language_word_dict.get("font_size"))
        self.font_size_combobox = QComboBox()
        for font_size in range(2, 101, 2):
            self.font_size_combobox.addItem(str(font_size))
        self.font_size_combobox.setCurrentText("16")
        self.font_size_combobox.currentTextChanged.connect(self.update_panel_text_size)
        # Buttons
        self.set_ai_config_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_set_ai_button"))
        self.set_ai_config_button.clicked.connect(self.set_ai_config)
        self.load_ai_config_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_load_ai_button"))
        self.load_ai_config_button.clicked.connect(lambda: self.load_ai_config(show_load_complete=True))
        self.call_ai_model_button = QPushButton(language_wrapper.language_word_dict.get("chat_ui_call_ai_model_button"))
        self.call_ai_model_button.clicked.connect(self.call_ai_model)
        # Add to layout
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.chat_panel_scroll_area, 0, 0, 1, 4)
        self.grid_layout.addWidget(self.call_ai_model_button, 1, 0)
        self.grid_layout.addWidget(self.font_size_combobox, 1, 1)
        self.grid_layout.addWidget(self.set_ai_config_button, 1, 2)
        self.grid_layout.addWidget(self.load_ai_config_button, 1, 3)
        self.grid_layout.addWidget(self.prompt_input, 2, 0, 1, 4)

        # Variable
        self.ai_config: AIConfig = ai_config
        self.lang_chain_interface: Union[LangChainInterface, None] = None
        self.set_ai_config_dialog = None
        # Timer to pop queue
        self.pull_message_timer = QTimer(self)
        self.pull_message_timer.setInterval(1000)
        self.pull_message_timer.timeout.connect(self.pull_message)
        self.pull_message_timer.start()

        # Set layout
        self.setLayout(self.grid_layout)

        self.load_ai_config()

    def update_panel_text_size(self):
        self.chat_panel.setFont(
            QFontDatabase.font(self.font().family(), "", int(self.font_size_combobox.currentText())))

    def load_ai_config(self, show_load_complete: bool = False):
        ai_config_file = Path(str(Path.cwd()) + "/" + ".jeditor/ai_config.json")
        if ai_config_file.exists():
            with open(ai_config_file, "r", encoding="utf-8"):
                json_data: dict = read_json(str(ai_config_file))
            if json_data:
                if json_data.get("AI_model") and len(json_data.get("AI_model")) == 4:
                    ai_info: dict = json_data.get("AI_model")
                    if ai_info.get("ai_base_url") and ai_info.get("chat_model"):
                        ai_config.choosable_ai.update(json_data)
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


    def call_ai_model(self):
        if isinstance(self.lang_chain_interface, LangChainInterface):
            thread = AskThread(lang_chain_interface=self.lang_chain_interface, prompt=self.prompt_input.text())
            thread.start()
        else:
            ai_info = ai_config.choosable_ai.get('AI_model')
            QMessageBox.warning(self,
                                language_wrapper.language_word_dict.get("call_ai_model_error_title"),
                                language_wrapper.language_word_dict.get(
                                    f"ai_api_key: {ai_info.get('ai_api_key')}, \n"
                                    f"ai_base_url: {ai_info.get('ai_base_url')}, \n"
                                    f"chat_model: {ai_info.get('chat_model')}, \n"
                                    f"prompt_template: {ai_info.get('prompt_template')}"))

    def pull_message(self):
        if not ai_config.message_queue.empty():
            ai_response = ai_config.message_queue.get_nowait()
            self.chat_panel.appendPlainText(ai_response)
            self.chat_panel.appendPlainText("\n")

    def set_ai_config(self):
        # Set and output AI a config file
        self.set_ai_config_dialog = SetAIDialog()
        self.set_ai_config_dialog.show()
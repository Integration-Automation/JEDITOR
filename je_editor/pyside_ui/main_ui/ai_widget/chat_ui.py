from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QScrollArea, QLabel, QComboBox, QGridLayout, QMessageBox

from je_editor import language_wrapper
from je_editor.pyside_ui.main_ui.ai_widget.ai_config import AIConfig
from je_editor.utils.json.json_file import read_json

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
        # Font size combobox
        self.font_size_label = QLabel(language_wrapper.language_word_dict.get("font_size"))
        self.font_size_combobox = QComboBox()
        for font_size in range(2, 101, 2):
            self.font_size_combobox.addItem(str(font_size))
        self.font_size_combobox.setCurrentText("16")
        self.font_size_combobox.currentTextChanged.connect(self.update_panel_text_size)
        # Add to layout
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.chat_panel_scroll_area, 1, 0, -1, -1)
        self.grid_layout.addWidget(self.font_size_combobox, 0, 1)
        # Read ai config json and set AI config
        ai_config = AIConfig()
        ai_config_file = Path(str(Path.cwd()) + "/" + ".jeditor/ai_config.json")
        if ai_config_file.exists():
            with open(ai_config_file, "r", encoding="utf-8") as file:
                json_data: dict = read_json(str(ai_config_file))
            if json_data:
                if json_data.get("AI_model") and len(json_data.get("AI_model")) == 3:
                    ai_info: dict = json_data.get("AI_model")
                    if ai_info.get("ai_base_url") and ai_info.get("ai_api_key") and ai_info.get("chat_model"):
                        ai_config.choosable_ai.update(json_data)
                    else:
                        QMessageBox.warning(self.main_window,
                                            language_wrapper.language_word_dict.get("set_ai_model_warring_title"),
                                            language_wrapper.language_word_dict.get("set_ai_model_warring_text"))

    def update_panel_text_size(self):
        self.chat_panel.setFont(
            QFontDatabase.font(self.font().family(), "", int(self.font_size_combobox.currentText())))

    def set_ai_config(self):
        # Set and output AI a config file
        pass

    def load_ai_config(self):
        # Load exists an AI config file
        pass

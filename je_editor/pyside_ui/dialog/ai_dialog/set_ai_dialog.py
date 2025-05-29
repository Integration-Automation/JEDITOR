from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QHBoxLayout, QPushButton, QMessageBox

from je_editor.pyside_ui.main_ui.ai_widget.ai_config import ai_config
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class SetAIDialog(QWidget):

    def __init__(self):
        jeditor_logger.info("Init SetAIDialog")
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.base_url_input = QLineEdit()
        self.api_key_input = QLineEdit()
        self.chat_model_input = QLineEdit()
        self.add_ai_info_button = QPushButton()
        self.add_ai_info_button.setText(language_wrapper.language_word_dict.get("add_ai_model_pushbutton"))
        self.add_ai_info_button.clicked.connect(self.update_ai_config)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.add_ai_info_button)
        self.box_layout.addWidget(self.base_url_input)
        self.box_layout.addWidget(self.api_key_input)
        self.box_layout.addWidget(self.chat_model_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle(language_wrapper.language_word_dict.get("add_ai_model_title"))
        self.setLayout(self.box_layout)

    def update_ai_config(self):
        base_url = self.base_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        chat_model = self.chat_model_input.text().strip()
        if base_url and chat_model:
            ai_config.choosable_ai.update(
                {"AI_model": {"base_url": base_url, "api_key": api_key, "chat_model": chat_model}}
            )
        else:
            QMessageBox.warning(self,
                                language_wrapper.language_word_dict.get("set_ai_model_warring_title"),
                                language_wrapper.language_word_dict.get("set_ai_model_warring_text"))

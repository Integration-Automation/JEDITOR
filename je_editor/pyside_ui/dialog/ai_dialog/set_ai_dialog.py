from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QHBoxLayout, QPushButton

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
        pass

from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QMessageBox, QGridLayout, QLabel

from je_editor.pyside_ui.main_ui.ai_widget.ai_config import ai_config
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class SetAIDialog(QWidget):
    """
    設定 AI 模型的對話框
    Dialog for configuring AI model settings
    """

    def __init__(self):
        jeditor_logger.info("Init SetAIDialog")
        super().__init__()

        # Base URL 輸入欄位 / Base URL input field
        self.base_url_label = QLabel(language_wrapper.language_word_dict.get("base_url_label"))
        self.base_url_input = QLineEdit()

        # API Key 輸入欄位 / API Key input field
        self.api_key_label = QLabel(language_wrapper.language_word_dict.get("api_key_label"))
        self.api_key_input = QLineEdit()

        # Chat Model 輸入欄位 / Chat model input field
        self.chat_model_label = QLabel(language_wrapper.language_word_dict.get("ai_model_label"))
        self.chat_model_input = QLineEdit()

        # 新增 AI 設定按鈕 / Button to add AI configuration
        self.add_ai_info_button = QPushButton()
        self.add_ai_info_button.setText(language_wrapper.language_word_dict.get("add_ai_model_pushbutton"))
        self.add_ai_info_button.clicked.connect(self.update_ai_config)

        # 使用 GridLayout 排版 / Use GridLayout for layout
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.base_url_label, 0, 0)
        self.grid_layout.addWidget(self.base_url_input, 0, 1)
        self.grid_layout.addWidget(self.api_key_label, 1, 0)
        self.grid_layout.addWidget(self.api_key_input, 1, 1)
        self.grid_layout.addWidget(self.chat_model_label, 2, 0)
        self.grid_layout.addWidget(self.chat_model_input, 2, 1)
        self.grid_layout.addWidget(self.add_ai_info_button, 3, 1)

        # 設定視窗標題 / Set window title
        self.setWindowTitle(language_wrapper.language_word_dict.get("add_ai_model_title"))
        self.setLayout(self.grid_layout)

    def update_ai_config(self):
        """
        更新 AI 設定，將使用者輸入的 base_url、api_key、chat_model
        儲存到 ai_config.choosable_ai 中
        Update AI configuration with user inputs (base_url, api_key, chat_model)
        """
        base_url = self.base_url_input.text().strip()
        api_key = self.api_key_input.text().strip()
        chat_model = self.chat_model_input.text().strip()

        if base_url and chat_model:
            # 更新設定字典 / Update configuration dictionary
            ai_config.choosable_ai.update(
                {"AI_model": {"base_url": base_url, "api_key": api_key, "chat_model": chat_model}}
            )
        else:
            # 若缺少必要欄位，顯示警告訊息框
            # Show warning message box if required fields are missing
            QMessageBox.warning(
                self,
                language_wrapper.language_word_dict.get("set_ai_model_warring_title"),
                language_wrapper.language_word_dict.get("set_ai_model_warring_text")
            )
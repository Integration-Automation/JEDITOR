from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QBoxLayout, QHBoxLayout

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class SearchBox(QWidget):
    """
    搜尋框元件
    Search box widget
    """

    def __init__(self):
        jeditor_logger.info("Init SearchBox")
        super().__init__()

        # 垂直佈局 (上到下)
        # Vertical layout (top to bottom)
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)

        # 搜尋輸入框 / Search input field
        self.search_input = QLineEdit()

        # 下一個搜尋按鈕 / Next search button
        self.search_next_button = QPushButton()
        self.search_next_button.setText(language_wrapper.language_word_dict.get("search_next_dialog_pushbutton"))

        # 上一個搜尋按鈕 / Previous search button
        self.search_back_button = QPushButton()
        self.search_back_button.setText(language_wrapper.language_word_dict.get("search_back_dialog_pushbutton"))

        # 水平佈局 (放置前後搜尋按鈕)
        # Horizontal layout (for back/next buttons)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.search_back_button)
        self.box_h_layout.addWidget(self.search_next_button)

        # 將元件加入主佈局
        # Add widgets to main layout
        self.box_layout.addWidget(self.search_input)
        self.box_layout.addLayout(self.box_h_layout)

        # 設定視窗標題 (支援多語系)
        # Set window title (multi-language support)
        self.setWindowTitle(language_wrapper.language_word_dict.get("search_box_dialog_title"))

        # 套用主佈局
        # Apply main layout
        self.setLayout(self.box_layout)
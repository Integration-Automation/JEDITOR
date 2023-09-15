from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QBoxLayout, QHBoxLayout

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class SearchBox(QWidget):

    def __init__(self):
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.search_input = QLineEdit()
        self.search_next_button = QPushButton()
        self.search_next_button.setText(language_wrapper.language_word_dict.get("dialog_search_next"))
        self.search_back_button = QPushButton()
        self.search_back_button.setText(language_wrapper.language_word_dict.get("dialog_search_back"))
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.search_back_button)
        self.box_h_layout.addWidget(self.search_next_button)
        self.box_layout.addWidget(self.search_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle("Search Text")
        self.setLayout(self.box_layout)

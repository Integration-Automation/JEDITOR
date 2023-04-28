from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QWidget, QLineEdit, QPushButton, QBoxLayout, QHBoxLayout


class SearchBox(QWidget):

    def __init__(self):
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.search_input = QLineEdit()
        self.search_next_button = QPushButton()
        self.search_next_button.setText("Search Next")
        self.search_back_button = QPushButton()
        self.search_back_button.setText("Search Back")
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.search_back_button)
        self.box_h_layout.addWidget(self.search_next_button)
        self.box_layout.addWidget(self.search_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle("Search Text")
        self.resize(150, 100)
        self.setLayout(self.box_layout)

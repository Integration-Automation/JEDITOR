from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QPushButton, QHBoxLayout


class CreateFileDialog(QWidget):

    def __init__(self):
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.file_name_input = QLineEdit()
        self.create_file_button = QPushButton()
        self.create_file_button.setText("Create File")
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.create_file_button)
        self.box_layout.addWidget(self.file_name_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle("Create File")
        self.setLayout(self.box_layout)

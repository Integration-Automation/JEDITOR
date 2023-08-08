from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox


class CreateFileDialog(QWidget):

    def __init__(self):
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.file_name_input = QLineEdit()
        self.create_file_button = QPushButton()
        self.create_file_button.setText("Create File")
        self.create_file_button.clicked.connect(self.create_file)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.create_file_button)
        self.box_layout.addWidget(self.file_name_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle("Create File")
        self.setLayout(self.box_layout)

    def create_file(self):
        file_name = self.file_name_input.text().strip()
        print("file_name: ", file_name)
        if file_name == "":
            create_file_message_box = QMessageBox(self)
            create_file_message_box.setText("Please enter right file name")
            create_file_message_box.show()
        else:
            with open(file_name, "w+") as file:
                file.write("")
            self.close()

from PySide6.QtWidgets import QWidget, QBoxLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class CreateFileDialog(QWidget):

    def __init__(self):
        jeditor_logger.info("Init CreateFileDialog")
        super().__init__()
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.file_name_input = QLineEdit()
        self.create_file_button = QPushButton()
        self.create_file_button.setText(language_wrapper.language_word_dict.get("dialog_create_file"))
        self.create_file_button.clicked.connect(self.create_file)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.create_file_button)
        self.box_layout.addWidget(self.file_name_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle(language_wrapper.language_word_dict.get("dialog_create_file"))
        self.setLayout(self.box_layout)

    def create_file(self):
        jeditor_logger.info("CreateFileDialog create_file")
        file_name = self.file_name_input.text().strip()
        if file_name == "":
            create_file_message_box = QMessageBox(self)
            create_file_message_box.setText(language_wrapper.language_word_dict.get("dialog_input_file_name"))
            create_file_message_box.show()
        else:
            with open(file_name, "w+") as file:
                file.write("")
            self.close()

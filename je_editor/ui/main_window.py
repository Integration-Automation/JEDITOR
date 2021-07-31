from PyQt5.QtWidgets import QMainWindow

from je_editor.ui.editor import Ui_MainWindow
from je_editor.utils.file.open_file_dialog import open_file
from je_editor.utils.text_process.exec_text import exec_code
from je_editor.utils.text_process.shell_text import run_on_shell


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.code_exec_pushbutton.clicked.connect(self.exec_code_connect)
        self.ui.shell_pushbutton.clicked.connect(self.run_on_shell_connect)
        self.ui.action_open_file.triggered.connect(self.open_file)

    def exec_code_connect(self):
        exec_code(self.ui.code_edit_plaintext.toPlainText(), self.ui.console_plaintext.setPlainText,
                  self.ui.console_plaintext.setPlainText)

    def run_on_shell_connect(self):
        run_on_shell(self.ui.code_edit_plaintext.toPlainText(), self.ui.console_plaintext.setPlainText,
                     self.ui.console_plaintext.setPlainText)

    def open_file(self):
        with open(open_file()[0], "r") as file:
            temp_string = file.read()
        self.ui.code_edit_plaintext.setPlainText(temp_string)

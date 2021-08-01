from PyQt5.QtWidgets import QMainWindow

from je_editor.ui.editor import Ui_MainWindow
from je_editor.utils.file.open_file import open_file
from je_editor.utils.file.save_file import save_file
from je_editor.utils.text_process.exec_text import exec_code
from je_editor.utils.text_process.shell_text import run_on_shell


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.code_exec_pushbutton.clicked.connect(self.exec_code_connect)
        self.ui.shell_pushbutton.clicked.connect(self.run_on_shell_connect)
        self.ui.action_open_file.triggered.connect(self.open_file_connect)
        self.ui.action_save_file.triggered.connect(self.save_file_connect)

    def exec_code_connect(self):
        exec_code(self.ui.code_edit_plaintext.toPlainText(), self.ui.console_plaintext.setPlainText,
                  self.ui.console_plaintext.setPlainText)

    def run_on_shell_connect(self):
        run_on_shell(self.ui.code_edit_plaintext.toPlainText(), self.ui.console_plaintext.setPlainText,
                     self.ui.console_plaintext.setPlainText)

    def open_file_connect(self):
        temp = open_file()
        if temp[0] != "":
            with open(temp[0], "r+") as file:
                self.ui.code_edit_plaintext.setPlainText(file.read())

    def save_file_connect(self):
        temp = save_file()
        if temp[0] != "":
            with open(temp[0], "w+") as file:
                file.write(self.ui.code_edit_plaintext.toPlainText())

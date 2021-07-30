import sys

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication

from je_editor.ui.main_window import MainWindow
from je_editor.utils.exception.je_editor_exceptions import except_hook


def start_je_editor():
    sys.excepthook = except_hook
    app = QApplication([])
    font = QFont("Times New Roman", 14)
    app.setFont(font)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

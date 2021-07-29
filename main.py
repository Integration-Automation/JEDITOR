import sys
from contextlib import redirect_stdout
from io import StringIO

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow

from editor import Ui_main_window


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_main_window()
        self.ui.setupUi(self)
        self.ui.test_button.clicked.connect(self.test_exec)

    def test_exec(self):
        try:
            exec_string_io = StringIO()
            with redirect_stdout(exec_string_io):
                exec(self.ui.code_edit.toPlainText())
            exec_result = exec_string_io.getvalue()
            self.ui.console.setPlainText(exec_result)
        except Exception as error:
            self.ui.console.setPlainText(str(error))
            raise error


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

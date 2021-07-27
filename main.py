import sys
from PyQt5.QtWidgets import QApplication,QMainWindow
from editor_main import Ui_MainWindow


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()


app = QApplication(sys.argv)
w = AppWindow()
w.show()
sys.exit(app.exec_())

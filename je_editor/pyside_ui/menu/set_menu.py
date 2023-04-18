from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMenuBar


def set_menu(ui_we_want_to_set: QMainWindow):
    # set menu
    ui_we_want_to_set.menu = QMenuBar()
    ui_we_want_to_set.file_menu = ui_we_want_to_set.menu.addMenu("File")
    # ui_we_want_to_set.test_action = QAction("test_action")
    # ui_we_want_to_set.test_action.triggered.connect(test)
    # ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.test_action)
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu("Run")
    ui_we_want_to_set.setMenuBar(ui_we_want_to_set.menu)


# def test():
#     print("test")

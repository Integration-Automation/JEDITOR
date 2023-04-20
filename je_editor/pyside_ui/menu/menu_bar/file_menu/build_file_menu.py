from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow


def set_file_menu(ui_we_want_to_set: QMainWindow):
    # TODO open file function
    ui_we_want_to_set.open_file_action = QAction("Open File")
    ui_we_want_to_set.open_file_action.triggered.connect(temp)
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.open_file_action)
    # TODO save file function
    ui_we_want_to_set.save_file_action = QAction("Save File")
    ui_we_want_to_set.save_file_action.triggered.connect(temp)
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.save_file_action)
    ui_we_want_to_set.file_menu.addSeparator()
    ui_we_want_to_set.file_menu.addMenu("Text")


def temp():
    print("temp")
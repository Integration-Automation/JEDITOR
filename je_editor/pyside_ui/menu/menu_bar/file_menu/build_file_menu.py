from PySide6.QtGui import QAction, QKeySequence, Qt
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.file_dialog.open_file_dialog import choose_file_get_open_filename
from je_editor.pyside_ui.file_dialog.save_file_dialog import choose_file_get_save_filename


def set_file_menu(ui_we_want_to_set: QMainWindow):
    ui_we_want_to_set.file_menu.open_file_action = QAction("Open File")
    ui_we_want_to_set.file_menu.open_file_action.setShortcut(
        QKeySequence(Qt.Key.Key_F, Qt.Key.Key_O)
    )
    ui_we_want_to_set.file_menu.open_file_action.triggered.connect(
        lambda: choose_file_get_open_filename(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_file_action)
    ui_we_want_to_set.file_menu.save_file_action = QAction("Save File")
    ui_we_want_to_set.file_menu.save_file_action.setShortcut(
        QKeySequence(Qt.Key.Key_F, Qt.Key.Key_S)
    )
    ui_we_want_to_set.file_menu.save_file_action.triggered.connect(
        lambda: choose_file_get_save_filename(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.save_file_action)



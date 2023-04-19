import os

from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.ui_setting.ui_setting import set_ui
from je_editor.pyside_ui.menu.set_menu import set_menu


class EditorMain(QMainWindow):

    def __init__(self):
        super(EditorMain, self).__init__()
        # set python buffered
        os.environ["PYTHONUNBUFFERED"] = "1"
        # Auto save thread
        self.auto_save_thread = None
        # current file
        self.current_file = None
        set_ui(self)
        set_menu(self)

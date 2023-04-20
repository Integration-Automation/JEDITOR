import os

from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.menu.menu_bar.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.treeview.project_treeview.set_project_treeview import set_project_treeview
from je_editor.pyside_ui.main_ui_setting.ui_setting import set_ui


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
        set_project_treeview(self)
        set_menu_bar(self)
        self.showMaximized()
        self.focusWidget()

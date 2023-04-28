import os

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QAction
from PySide6.QtWidgets import QMainWindow

from je_editor.pyside_ui.auto_save.auto_save_thread import SaveThread
from je_editor.pyside_ui.colors.global_color import error_color, output_color
from je_editor.pyside_ui.main_ui_setting.ui_setting import set_ui
from je_editor.pyside_ui.menu.menu_bar.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.treeview.project_treeview.set_project_treeview import set_project_treeview
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance


class EditorMain(QMainWindow):

    def __init__(self):
        super(EditorMain, self).__init__()
        # set python buffered
        os.environ["PYTHONUNBUFFERED"] = "1"
        # Auto save thread
        self.auto_save_thread = None
        # current file
        self.current_file = None
        # Font
        self.font_database = QFontDatabase()
        # Color
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(1)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()
        set_ui(self)
        set_project_treeview(self)
        set_menu_bar(self)
        self.add_font_menu()
        self.add_font_size_menu()
        self.showMaximized()
        self.focusWidget()
        if self.current_file is not None and self.auto_save_thread is None:
            self.auto_save_thread = SaveThread(
                self.current_file,
                self.code_edit.code_edit.toPlainText()
            )
            self.auto_save_thread.start()
        redirect_manager_instance.set_redirect(self, True)

    def add_font_menu(self):
        self.font_menu = self.text_menu.addMenu("Font")
        for family in self.font_database.families():
            font_action = QAction(family, parent=self)
            font_action.triggered.connect(self.set_font)
            self.font_menu.addAction(font_action)

    def add_font_size_menu(self):
        self.font_size_menu = self.text_menu.addMenu("Font Size")
        for size in range(12, 38, 2):
            font_action = QAction(str(size), parent=self)
            font_action.triggered.connect(self.set_font_size)
            self.font_size_menu.addAction(font_action)

    def set_font(self):
        self.code_edit.setFont(
            self.font_database.font(
                self.sender().text(),
                "",
                self.code_edit.font().pointSize()
            )
        )
        self.code_result.setFont(
            self.font_database.font(
                self.sender().text(),
                "",
                self.code_result.font().pointSize()
            )
        )

    def set_font_size(self):
        self.code_edit.setFont(
            self.font_database.font(
                self.code_edit.font().family(),
                "",
                int(self.sender().text())
            )
        )
        self.code_result.setFont(
            self.font_database.font(
                self.code_result.font().family(),
                "",
                int(self.sender().text())
            )
        )

    def redirect(self):
        if self.auto_save_thread is not None:
            self.auto_save_thread.text_to_write = self.code_edit.toPlainText()
        if not redirect_manager_instance.std_out_queue.empty():
            output_message = redirect_manager_instance.std_out_queue.get()
            output_message = str(output_message).strip()
            if output_message:
                self.code_result.append(output_message)
        self.code_result.setTextColor(error_color)
        if not redirect_manager_instance.std_err_queue.empty():
            error_message = redirect_manager_instance.std_err_queue.get_nowait()
            error_message = str(error_message).strip()
            if error_message:
                self.code_result.append(error_message)
        self.code_result.setTextColor(output_color)

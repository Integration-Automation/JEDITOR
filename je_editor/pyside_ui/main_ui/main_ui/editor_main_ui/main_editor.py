import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QGridLayout, QTabWidget
from frontengine import FrontEngineMainUI, ChatSceneUI
from qt_material import QtStyleTools

from je_editor.pyside_ui.code.auto_save.auto_save_thread import SaveThread
from je_editor.pyside_ui.code.shell_process.shell_exec import default_shell_manager
from je_editor.pyside_ui.colors.global_color import error_color, output_color
from je_editor.pyside_ui.main_ui.main_ui_setting.ui_setting import set_ui
from je_editor.pyside_ui.main_ui.menu.menu_bar.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.main_ui.save_user_setting.user_setting_file import write_user_setting, \
    user_setting_dict, read_user_setting
from je_editor.pyside_ui.main_ui.system_tray.extend_system_tray import ExtendSystemTray
from je_editor.pyside_ui.main_ui.treeview.project_treeview.set_project_treeview import set_project_treeview
from je_editor.utils.encodings.python_encodings import python_encodings_list
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance


class EditorMain(QMainWindow, QtStyleTools):

    def __init__(self, debug_mode: bool = False, **kwargs):
        super(EditorMain, self).__init__()
        # Debug mode
        self.debug_mode: bool = debug_mode
        # Windows setup
        self.id = "JEditor"
        # Venv
        self.venv_path = None
        if sys.platform in ["win32", "cygwin", "msys"]:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.id)
        # set python buffered
        os.environ["PYTHONUNBUFFERED"] = "1"
        # Auto save thread
        self.auto_save_thread = None
        # current file
        self.current_file = None
        # Encoding
        self.encoding = "utf-8"
        # Font
        self.font_database = QFontDatabase()
        # TabWidget
        self.tab_widget = QTabWidget()
        # MainWidget
        self.main_widget = QWidget()
        self.grid_layout = QGridLayout(self.main_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(1)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()
        set_ui(self)
        set_project_treeview(self)
        set_menu_bar(self)
        # Set font and font size menu
        self.add_font_menu()
        self.add_font_size_menu()
        # Set encoding menu
        self.add_encoding_menu()
        if self.current_file is not None and self.auto_save_thread is None:
            self.auto_save_thread = SaveThread(
                self.current_file,
                self.code_edit.code_edit.toPlainText()
            )
            self.auto_save_thread.start()
        # Set Icon
        self.icon_path = Path(os.getcwd() + "/je_driver_icon.ico")
        self.icon = QIcon(str(self.icon_path))
        if self.icon.isNull() is False:
            self.setWindowIcon(self.icon)
            if ExtendSystemTray.isSystemTrayAvailable():
                self.system_tray = ExtendSystemTray(main_window=self)
                self.system_tray.setIcon(self.icon)
                self.system_tray.show()
        # Init shell manager
        default_shell_manager.main_window = self
        default_shell_manager.later_init()
        # Put Redirect on last to trace exception
        redirect_manager_instance.set_redirect(self, True)
        # Add style menu
        self.add_style_menu()
        # TAB Add
        self.tab_widget.addTab(self.main_widget, "Editor")
        self.tab_widget.addTab(ChatSceneUI(), "Chat")
        self.tab_widget.addTab(FrontEngineMainUI(), "FrontEngine")
        self.setCentralWidget(self.tab_widget)
        # If debug open 10s and close
        if self.debug_mode:
            close_timer = QTimer(self)
            close_timer.setInterval(10000)
            close_timer.timeout.connect(self.debug_close)
            close_timer.start()

    def add_style_menu(self) -> None:
        self.menu.style_menu = self.menu.addMenu("UI Style")
        for style in [
            'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml', 'dark_lightgreen.xml', 'dark_pink.xml',
            'dark_purple.xml', 'dark_red.xml', 'dark_teal.xml', 'dark_yellow.xml', 'light_amber.xml',
            'light_blue.xml', 'light_cyan.xml', 'light_cyan_500.xml', 'light_lightgreen.xml',
            'light_pink.xml', 'light_purple.xml', 'light_red.xml', 'light_teal.xml', 'light_yellow.xml'
        ]:
            change_style_action = QAction(style, parent=self)
            change_style_action.triggered.connect(self.set_style)
            self.menu.style_menu.addAction(change_style_action)

    def set_style(self) -> None:
        self.apply_stylesheet(self, self.sender().text())

    def startup_setting(self) -> None:
        # Set font and font size, then try to open last edit file
        read_user_setting()
        self.code_edit.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        self.code_result.setStyleSheet(
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        last_file = user_setting_dict.get("last_file", None)
        if last_file is not None:
            last_file_path = Path(last_file)
            if last_file_path.is_file() and last_file_path.exists():
                self.current_file = str(last_file_path)
                self.code_edit.setPlainText(read_file(self.current_file)[1])

    def add_font_menu(self) -> None:
        self.font_menu = self.text_menu.addMenu("Font")
        for family in self.font_database.families():
            font_action = QAction(family, parent=self)
            font_action.triggered.connect(self.set_font)
            self.font_menu.addAction(font_action)

    def add_font_size_menu(self) -> None:
        self.font_size_menu = self.text_menu.addMenu("Font Size")
        for size in range(12, 38, 2):
            font_action = QAction(str(size), parent=self)
            font_action.triggered.connect(self.set_font_size)
            self.font_size_menu.addAction(font_action)

    def set_font(self) -> None:
        self.code_edit.setStyleSheet(
            f"font-size: {self.code_edit.font().pointSize()}pt;"
            f"font-family: {self.sender().text()};"
        )
        self.code_result.setStyleSheet(
            f"font-size: {self.code_result.font().pointSize()}pt;"
            f"font-family: {self.sender().text()};"
        )
        user_setting_dict.update({"font": self.sender().text()})

    def set_font_size(self) -> None:
        self.code_edit.setStyleSheet(
            f"font-size: {int(self.sender().text())}pt;"
            f"font-family: {self.code_edit.font().family()};"
        )
        self.code_result.setStyleSheet(
            f"font-size: {int(self.sender().text())}pt;"
            f"font-family: {self.code_result.font().family()};"
        )
        user_setting_dict.update({"font_size": int(self.sender().text())})

    def add_encoding_menu(self) -> None:
        self.encoding_menu = self.file_menu.addMenu("Encodings")
        for encoding in python_encodings_list:
            encoding_action = QAction(encoding, parent=self)
            encoding_action.triggered.connect(self.set_encoding)
            self.encoding_menu.addAction(encoding_action)

    def set_encoding(self) -> None:
        self.encoding = self.sender().text()
        user_setting_dict.update({"encoding": self.sender().text()})

    def redirect(self) -> None:
        # Pull out redirect text and put text in code result area
        if self.auto_save_thread is not None:
            self.auto_save_thread.text_to_write = self.code_edit.toPlainText()
        if not redirect_manager_instance.std_out_queue.empty():
            output_message = redirect_manager_instance.std_out_queue.get_nowait()
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

    def closeEvent(self, event) -> None:
        if self.system_tray.isVisible():
            self.hide()
            event.ignore()
        else:
            super().closeEvent(event)
            user_setting_dict.update({"last_file": str(self.current_file)})
            write_user_setting()

    @classmethod
    def debug_close(cls):
        sys.exit(0)

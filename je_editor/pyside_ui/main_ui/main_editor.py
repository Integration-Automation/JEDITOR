import os
import pathlib
import sys
from pathlib import Path
from typing import Dict, Type

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase, QAction, QIcon
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget
from frontengine import FrontEngineMainUI
from frontengine import RedirectManager
from qt_material import QtStyleTools

from je_editor.pyside_ui.browser.browser_widget import JEBrowser
from je_editor.pyside_ui.colors.global_color import error_color, output_color
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.menu.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.main_ui.save_user_setting.user_setting_file import user_setting_dict, read_user_setting, \
    write_user_setting
from je_editor.pyside_ui.main_ui.system_tray.extend_system_tray import ExtendSystemTray
from je_editor.utils.encodings.python_encodings import python_encodings_list
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance

EDITOR_EXTEND_TAB: Dict[str, Type[QWidget]] = {}


class EditorMain(QMainWindow, QtStyleTools):

    def __init__(self, debug_mode: bool = False, show_system_tray_ray: bool = True):
        super(EditorMain, self).__init__()
        # Init variable
        self.file_menu = None
        self.text_menu = None
        self.code_result = None
        self.code_edit = None
        self.menu = None
        self.encoding_menu = None
        self.font_size_menu = None
        self.font_menu = None
        # Project compiler if user not choose this will use which to find
        self.python_compiler = None
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
        # Encoding
        self.encoding = "utf-8"
        # Font
        self.font_database = QFontDatabase()
        # TabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.tab_widget.removeTab)
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(1)
        self.redirect_timer.start()
        self.setWindowTitle("JEditor")
        set_menu_bar(self)
        # Set font and font size menu
        self.add_font_menu()
        self.add_font_size_menu()
        # Set encoding menu
        self.add_encoding_menu()
        # Set Icon
        self.icon_path = Path(os.getcwd() + "/je_driver_icon.ico")
        self.icon = QIcon(str(self.icon_path))
        if self.icon.isNull() is False:
            self.setWindowIcon(self.icon)
            if ExtendSystemTray.isSystemTrayAvailable() and show_system_tray_ray:
                self.system_tray = ExtendSystemTray(main_window=self)
                self.system_tray.setIcon(self.icon)
                self.system_tray.setVisible(True)
                self.system_tray.show()
                self.system_tray.setToolTip("JEditor")
        # Put Redirect on last to trace exception
        RedirectManager.restore_std()
        redirect_manager_instance.set_redirect(self, True)
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(1)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()
        # Add style menu
        self.add_style_menu()
        # TAB Add
        self.tab_widget.addTab(EditorWidget(), "Editor")
        self.tab_widget.addTab(FrontEngineMainUI(show_system_tray_ray=False), "FrontEngine")
        self.tab_widget.addTab(JEBrowser(), "Web Browser")
        for widget_name, widget in EDITOR_EXTEND_TAB.items():
            self.tab_widget.addTab(widget(), widget_name)
        self.setCentralWidget(self.tab_widget)
        # If debug open 10s and close
        if self.debug_mode:
            close_timer = QTimer(self)
            close_timer.setInterval(10000)
            close_timer.timeout.connect(self.debug_close)
            close_timer.start()

    def set_font(self) -> None:
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                widget.setStyleSheet(
                    f"font-size: {widget.code_edit.font().pointSize()}pt;"
                    f"font-family: {self.sender().text()};"
                )
                widget.setStyleSheet(
                    f"font-size: {widget.code_result.font().pointSize()}pt;"
                    f"font-family: {self.sender().text()};"
                )
                user_setting_dict.update({"font": self.sender().text()})

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

    def set_font_size(self) -> None:
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if type(widget) is EditorWidget:
                widget.code_edit.setStyleSheet(
                    f"font-size: {int(self.sender().text())}pt;"
                    f"font-family: {widget.code_edit.font().family()};"
                )
                widget.code_result.setStyleSheet(
                    f"font-size: {int(self.sender().text())}pt;"
                    f"font-family: {widget.code_result.font().family()};"
                )
                user_setting_dict.update({"font_size": int(self.sender().text())})

    def clear_code_result(self):
        widget = self.tab_widget.currentWidget()
        if type(widget) is EditorWidget:
            widget.code_result.clear()

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
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if type(widget) is EditorWidget:
                # Pull out redirect text and put text in code result area
                if widget.auto_save_thread is not None:
                    widget.auto_save_thread.text_to_write = widget.code_edit.toPlainText()
                if not redirect_manager_instance.std_out_queue.empty():
                    output_message = redirect_manager_instance.std_out_queue.get_nowait()
                    output_message = str(output_message).strip()
                    if output_message:
                        widget.code_result.append(output_message)
                widget.code_result.setTextColor(error_color)
                if not redirect_manager_instance.std_err_queue.empty():
                    error_message = redirect_manager_instance.std_err_queue.get_nowait()
                    error_message = str(error_message).strip()
                    if error_message:
                        widget.code_result.append(error_message)
                widget.code_result.setTextColor(output_color)
                break

    def startup_setting(self) -> None:
        # Set font and font size, then try to open last edit file
        read_user_setting()
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                widget.code_edit.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                widget.code_result.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                self.python_compiler = user_setting_dict.get("python_compiler", None)
                last_file = user_setting_dict.get("last_file", None)
                if last_file is not None:
                    last_file_path = pathlib.Path(last_file)
                    if last_file_path.is_file() and last_file_path.exists():
                        widget.current_file = str(last_file_path)
                        widget.code_edit.setPlainText(read_file(widget.current_file)[1])

    def closeEvent(self, event) -> None:
        if self.system_tray.isVisible():
            self.hide()
            event.ignore()
        else:
            write_user_setting()
            super().closeEvent(event)

    @classmethod
    def debug_close(cls):
        sys.exit(0)

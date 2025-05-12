import os
import pathlib
import sys
from pathlib import Path
from typing import Dict, Type

import jedi.settings
from PySide6.QtCore import QTimer, QEvent
from PySide6.QtGui import QFontDatabase, QIcon, Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QMessageBox
from frontengine import FrontEngineMainUI
from qt_material import QtStyleTools

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.pyside_ui.code.auto_save.auto_save_manager import init_new_auto_save_thread, file_is_open_manager_dict
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.menu.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import write_user_color_setting, \
    read_user_color_setting, update_actually_color_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict, read_user_setting, \
    write_user_setting
from je_editor.pyside_ui.main_ui.system_tray.extend_system_tray import ExtendSystemTray
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance

EDITOR_EXTEND_TAB: Dict[str, Type[QWidget]] = {}


class EditorMain(QMainWindow, QtStyleTools):

    def __init__(self, debug_mode: bool = False, show_system_tray_ray: bool = False):
        jeditor_logger.info(f"Init EditorMain "
                            f"debug_mode: {debug_mode} "
                            f"show_system_tray_ray: {show_system_tray_ray}")
        super(EditorMain, self).__init__()
        # Init variable
        self.file_menu = None
        self.code_result = None
        self.code_edit = None
        self.menu = None
        self.encoding_menu = None
        self.font_size_menu = None
        self.font_menu = None
        self.working_dir = None
        self.show_system_tray_ray = show_system_tray_ray
        # Self attr
        # Read user setting first
        read_user_setting()
        # Set language
        language_wrapper.reset_language(user_setting_dict.get("language", "English"))
        # Jedi run on thread safe
        jedi.settings.fast_parser = False
        # Jedi only show right case_insensitive
        jedi.settings.case_insensitive_completion = False
        # Project compiler if user not choose this will use which to find
        self.python_compiler = None
        # Debug mode
        self.debug_mode: bool = debug_mode
        # Windows setup
        self.id = language_wrapper.language_word_dict.get("application_name")
        if sys.platform in ["win32", "cygwin", "msys"]:
            from ctypes import windll
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.id)
        # set python buffered
        os.environ["PYTHONUNBUFFERED"] = "1"
        # Auto save thread
        self.auto_save_thread = None
        # Encoding
        self.encoding = "utf-8"
        read_user_color_setting()
        # Font
        self.font_database = QFontDatabase()
        # TabWidget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, on=False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(10)
        self.redirect_timer.start()
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))
        self.setToolTip(language_wrapper.language_word_dict.get("application_name"))
        set_menu_bar(self)
        # Set Icon
        self.icon_path = Path(os.getcwd() + "/je_driver_icon.ico")
        self.icon = QIcon(str(self.icon_path))
        if self.icon.isNull() is False:
            self.setWindowIcon(self.icon)
            if ExtendSystemTray.isSystemTrayAvailable() and self.show_system_tray_ray:
                self.system_tray = ExtendSystemTray(main_window=self)
                self.system_tray.setIcon(self.icon)
                self.system_tray.setVisible(True)
                self.system_tray.show()
                self.system_tray.setToolTip(language_wrapper.language_word_dict.get("application_name"))
        # Put Redirect on last to trace exception
        redirect_manager_instance.restore_std()
        redirect_manager_instance.set_redirect()
        # Timer to redirect error or message
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(10)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()
        # TAB Add
        self.tab_widget.addTab(EditorWidget(self), language_wrapper.language_word_dict.get("tab_name_editor"))
        self.tab_widget.addTab(
            FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False),
            language_wrapper.language_word_dict.get("tab_name_frontengine"))
        self.tab_widget.addTab(BrowserWidget(), language_wrapper.language_word_dict.get("tab_name_web_browser"))
        self.tab_widget.addTab(
            BrowserWidget(start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="),
            language_wrapper.language_word_dict.get("tab_menu_stackoverflow_tab_name"))
        for widget_name, widget in EDITOR_EXTEND_TAB.items():
            self.tab_widget.addTab(widget(), widget_name)
        self.setCentralWidget(self.tab_widget)
        # Read Setting
        self.startup_setting()
        # If debug open 10s and close
        if self.debug_mode:
            close_timer = QTimer(self)
            close_timer.setInterval(10000)
            close_timer.timeout.connect(self.debug_close)
            close_timer.start()

    def clear_code_result(self):
        jeditor_logger.info(f"EditorMain clear_code_result")
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            widget.code_result.clear()

    def redirect(self) -> None:
        jeditor_logger.info(f"EditorMain redirect")
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                # Pull out redirect text and put text in code result area
                if not redirect_manager_instance.std_out_queue.empty():
                    output_message = redirect_manager_instance.std_out_queue.get_nowait()
                    output_message = str(output_message).strip()
                    if output_message:
                        widget.code_result.append(output_message)
                widget.code_result.setTextColor(Qt.GlobalColor.red)
                if not redirect_manager_instance.std_err_queue.empty():
                    error_message = redirect_manager_instance.std_err_queue.get_nowait()
                    error_message = str(error_message).strip()
                    if error_message:
                        widget.code_result.append(error_message)
                widget.code_result.setTextColor(Qt.GlobalColor.black)
                break

    def startup_setting(self) -> None:
        jeditor_logger.info(f"EditorMain startup_setting")
        # Set font and font size, then try to open last edit file
        self.setStyleSheet(
            f"font-size: {user_setting_dict.get('ui_font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('ui_font', 'Lato')};"
        )
        # User setting
        for code_editor_count in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor_count)
            if isinstance(widget, EditorWidget):
                # Font size
                widget.code_edit.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                # Font
                widget.code_result.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                # Default compiler
                self.python_compiler = user_setting_dict.get("python_compiler", None)
                # Last edit file
                last_file = user_setting_dict.get("last_file", None)
                if last_file is not None:
                    last_file_path = pathlib.Path(last_file)
                    if last_file_path.is_file() and last_file_path.exists() and widget.code_save_thread is None:
                        init_new_auto_save_thread(str(last_file_path), widget)
                        widget.code_edit.setPlainText(read_file(widget.current_file)[1])
                        widget.code_edit.current_file = widget.current_file
                        widget.code_edit.reset_highlighter()
                        file_is_open_manager_dict.update({str(last_file_path): str(last_file_path.name)})
                        widget.rename_self_tab()

        # Style
        self.apply_stylesheet(self, user_setting_dict.get("ui_style", "dark_amber.xml"))
        # Color
        update_actually_color_dict()

    def go_to_new_tab(self, file_path: Path):
        jeditor_logger.info(f"EditorMain go_to_new_tab file_path: {file_path}")
        if file_is_open_manager_dict.get(str(file_path), None) is None:
            editor_widget = EditorWidget(self)
            self.tab_widget.addTab(
                editor_widget,
                f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
                f"{self.tab_widget.count()}")
            self.tab_widget.setCurrentWidget(editor_widget)
            editor_widget.open_an_file(file_path)
        else:
            widget: QWidget = self.tab_widget.findChild(EditorWidget, str(file_path))
            self.tab_widget.setCurrentWidget(widget)

    def closeEvent(self, event) -> None:
        jeditor_logger.info("EditorMain closeEvent")
        write_user_setting()
        write_user_color_setting()
        super().closeEvent(event)

    def event(self, event: QEvent) -> bool:
        jeditor_logger.info(f"EditorMain event: {event}")
        if event.type() == QEvent.Type.ToolTip:
            event.ignore()
            return False
        else:
            return super().event(event)

    def close_tab(self, index: int):
        widget = self.tab_widget.widget(index)
        if widget:
            widget.close()
        self.tab_widget.removeTab(index)

    @classmethod
    def debug_close(cls):
        sys.exit(0)

import os
import pathlib
import sys
from pathlib import Path
from typing import Dict, Type

# 匯入 Jedi 設定，用於 Python 自動補全與分析
# Import Jedi settings for Python auto-completion and analysis
import jedi.settings
# 匯入 PySide6 (Qt for Python) 的核心模組
# Import PySide6 core modules
from PySide6.QtCore import QTimer, QEvent
from PySide6.QtGui import QFontDatabase, QIcon, Qt, QTextCharFormat
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget
# 匯入 Qt Material 主題工具
# Import Qt Material style tools
from qt_material import QtStyleTools

# 匯入專案內部模組 (自訂 UI 與功能)
# Import project-specific modules (custom UI and features)
from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget
from je_editor.pyside_ui.code.auto_save.auto_save_manager import init_new_auto_save_thread, file_is_open_manager_dict
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.menu.set_menu_bar import set_menu_bar
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import (
    write_user_color_setting,
    read_user_color_setting,
    update_actually_color_dict,
    actually_color_dict
)
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import (
    user_setting_dict,
    read_user_setting,
    write_user_setting
)
from je_editor.pyside_ui.main_ui.system_tray.extend_system_tray import ExtendSystemTray
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance

# 定義一個字典，用來存放可擴充的 Tab (標籤頁)
# Define a dictionary to store extendable tabs
EDITOR_EXTEND_TAB: Dict[str, Type[QWidget]] = {}


class EditorMain(QMainWindow, QtStyleTools):
    """
    主編輯器視窗類別
    Main editor window class
    繼承 QMainWindow 與 QtStyleTools
    """

    def __init__(self, debug_mode: bool = False, show_system_tray_ray: bool = False, extend: bool = False):
        # 初始化時記錄 log
        # Log initialization
        jeditor_logger.info(f"Init EditorMain "
                            f"debug_mode: {debug_mode} "
                            f"show_system_tray_ray: {show_system_tray_ray}")
        super(EditorMain, self).__init__()

        # 初始化變數
        # Initialize variables
        self.file_menu = None
        self.code_result = None
        self.code_edit = None
        self.menu = None
        self.encoding_menu = None
        self.font_size_menu = None
        self.font_menu = None
        self.working_dir = None
        self.show_system_tray_ray = show_system_tray_ray

        # 讀取使用者設定
        # Read user settings
        read_user_setting()

        # 設定語言 (多語系支援)
        # Set language (multi-language support)
        language_wrapper.reset_language(user_setting_dict.get("language", "English"))

        # Jedi 設定：關閉快取解析器，避免執行緒問題
        # Jedi settings: disable fast parser for thread safety
        jedi.settings.fast_parser = False
        jedi.settings.case_insensitive_completion = False  # 關閉大小寫不敏感補全 / Disable case-insensitive completion

        # Python 編譯器 (可由使用者指定)
        # Python compiler (can be set by user)
        self.python_compiler = None

        # 除錯模式
        # Debug mode
        self.debug_mode: bool = debug_mode

        # Windows 系統專用：設定應用程式 ID
        # Windows only: set application ID
        if not extend:
            self.id = language_wrapper.language_word_dict.get("application_name")
            if sys.platform in ["win32", "cygwin", "msys"]:
                from ctypes import windll
                windll.shell32.SetCurrentProcessExplicitAppUserModelID(self.id)

        # 設定 Python 輸出不緩衝
        # Set Python output unbuffered
        os.environ["PYTHONUNBUFFERED"] = "1"

        # 自動儲存執行緒
        # Auto-save thread
        self.auto_save_thread = None

        # 預設編碼
        # Default encoding
        self.encoding = "utf-8"

        # 讀取使用者顏色設定
        # Read user color settings
        read_user_color_setting()

        # 字型資料庫
        # Font database
        self.font_database = QFontDatabase()

        # 建立 TabWidget (多分頁編輯器)
        # Create TabWidget (multi-tab editor)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)  # 可關閉分頁 / Tabs closable
        self.tab_widget.setAttribute(Qt.WidgetAttribute.WA_AlwaysShowToolTips, on=False)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

        # 建立計時器，用來處理訊息重導 (stdout/stderr)
        # Timer for redirecting messages (stdout/stderr)
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(10)
        self.redirect_timer.start()

        # 設定視窗標題與提示
        # Set window title and tooltip
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))
        self.setToolTip(language_wrapper.language_word_dict.get("application_name"))

        # 設定選單列
        # Set menu bar
        set_menu_bar(self)

        # 設定應用程式圖示
        # Set application icon
        if not extend:
            self.icon_path = Path(os.getcwd() + "/python_editor.ico")
            self.icon = QIcon(str(self.icon_path))
            if not self.icon.isNull():
                self.setWindowIcon(self.icon)
                # 如果系統支援系統匣，則顯示圖示
                # Show system tray icon if available
                if ExtendSystemTray.isSystemTrayAvailable() and self.show_system_tray_ray:
                    self.system_tray = ExtendSystemTray(main_window=self)
                    self.system_tray.setIcon(self.icon)
                    self.system_tray.setVisible(True)
                    self.system_tray.show()
                    self.system_tray.setToolTip(language_wrapper.language_word_dict.get("application_name"))

        # 設定輸出重導 (stdout/stderr)
        # Setup output redirection (stdout/stderr)
        redirect_manager_instance.restore_std()
        redirect_manager_instance.set_redirect()

        # 再次設定計時器，定期檢查輸出
        # Setup timer again to check redirected output
        self.redirect_timer = QTimer(self)
        self.redirect_timer.setInterval(10)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()

        # 建立主要分頁：編輯器與瀏覽器
        # Create main tabs: editor and browser
        main_browser_widget = MainBrowserWidget()
        self.tab_widget.addTab(EditorWidget(self), language_wrapper.language_word_dict.get("tab_name_editor"))
        self.tab_widget.addTab(main_browser_widget, language_wrapper.language_word_dict.get("tab_name_web_browser"))

        # 預設新增一個 StackOverflow 瀏覽分頁
        # Add a default StackOverflow browser tab
        main_browser_widget.add_browser_tab(
            BrowserWidget(start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="))

        # 加入擴充的自訂分頁
        # Add extended custom tabs
        for widget_name, widget in EDITOR_EXTEND_TAB.items():
            self.tab_widget.addTab(widget(), widget_name)

        # 設定中央元件為 TabWidget
        # Set central widget as TabWidget
        self.setCentralWidget(self.tab_widget)

        # 啟動時讀取設定
        # Load startup settings
        self.startup_setting()

        # 如果是 debug 模式，10 秒後自動關閉
        # If debug mode, auto-close after 10 seconds
        if self.debug_mode:
            close_timer = QTimer(self)
            close_timer.setInterval(10000)
            close_timer.timeout.connect(self.debug_close)
            close_timer.start()

    def clear_code_result(self):
        """
        清除目前編輯器的輸出結果
        Clear the current editor's output result
        """
        jeditor_logger.info(f"EditorMain clear_code_result")
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            widget.code_result.clear()

    def redirect(self) -> None:
        """
        將 stdout/stderr 的訊息導入到編輯器的輸出區域
        Redirect stdout/stderr messages into the editor's output area
        """
        jeditor_logger.info(f"EditorMain redirect")
        # 遍歷所有分頁 (Tab)，尋找 EditorWidget
        # Iterate through all tabs to find EditorWidget
        for code_editor in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                # stdout 輸出處理
                # Handle stdout messages
                if not redirect_manager_instance.std_out_queue.empty():
                    output_message = redirect_manager_instance.std_out_queue.get_nowait()
                    output_message = str(output_message).strip()
                    if output_message:
                        text_cursor = self.code_result.textCursor()
                        text_format = QTextCharFormat()
                        # 設定正常輸出顏色
                        # Set normal output color
                        text_format.setForeground(actually_color_dict.get("normal_output_color"))
                        text_cursor.insertText(output_message, text_format)
                        text_cursor.insertBlock()

                # stderr 錯誤輸出處理
                # Handle stderr messages
                if not redirect_manager_instance.std_err_queue.empty():
                    error_message = redirect_manager_instance.std_err_queue.get_nowait()
                    error_message = str(error_message).strip()
                    if error_message:
                        text_cursor = self.code_result.textCursor()
                        text_format = QTextCharFormat()
                        # 設定錯誤輸出顏色
                        # Set error output color
                        text_format.setForeground(actually_color_dict.get("error_output_color"))
                        text_cursor.insertText(error_message, text_format)
                        text_cursor.insertBlock()
                break  # 找到第一個 EditorWidget 就結束迴圈 / Stop after first EditorWidget found

    def startup_setting(self) -> None:
        """
        啟動時套用使用者設定 (字型、樣式、上次開啟的檔案)
        Apply user settings on startup (fonts, styles, last opened file)
        """
        jeditor_logger.info(f"EditorMain startup_setting")
        # 設定 UI 字型與大小
        # Set UI font and size
        self.setStyleSheet(
            f"font-size: {user_setting_dict.get('ui_font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('ui_font', 'Lato')};"
        )

        # 套用到每個編輯器分頁
        # Apply settings to each editor tab
        for code_editor_count in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor_count)
            if isinstance(widget, EditorWidget):
                # 編輯區字型
                # Font for code editor
                widget.code_edit.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                # 輸出區字型
                # Font for output area
                widget.code_result.setStyleSheet(
                    f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
                    f"font-family: {user_setting_dict.get('font', 'Lato')};"
                )
                # 預設 Python 編譯器
                # Default Python compiler
                self.python_compiler = user_setting_dict.get("python_compiler", None)

                # 嘗試開啟上次編輯的檔案
                # Try to open last edited file
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

        # 套用 UI 樣式 (主題)
        # Apply UI stylesheet (theme)
        self.apply_stylesheet(self, user_setting_dict.get("ui_style", "dark_amber.xml"))
        # 更新顏色設定
        # Update color settings
        update_actually_color_dict()

    def go_to_new_tab(self, file_path: Path):
        """
        開啟新分頁並載入檔案
        Open a new tab and load a file
        """
        jeditor_logger.info(f"EditorMain go_to_new_tab file_path: {file_path}")
        if file_is_open_manager_dict.get(str(file_path), None) is None:
            # 建立新的編輯器分頁
            # Create a new editor tab
            editor_widget = EditorWidget(self)
            self.tab_widget.addTab(
                editor_widget,
                f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
                f"{self.tab_widget.count()}"
            )
            self.tab_widget.setCurrentWidget(editor_widget)
            editor_widget.open_an_file(file_path)
        else:
            # 如果檔案已開啟，直接切換到該分頁
            # If file already opened, switch to that tab
            widget: QWidget = self.tab_widget.findChild(EditorWidget, str(file_path))
            self.tab_widget.setCurrentWidget(widget)

    def closeEvent(self, event) -> None:
        """
        視窗關閉事件：儲存使用者設定
        Window close event: save user settings
        """
        jeditor_logger.info("EditorMain closeEvent")
        write_user_setting()
        write_user_color_setting()
        super().closeEvent(event)

    def event(self, event: QEvent) -> bool:
        """
        事件處理：忽略 ToolTip 類型事件
        Event handler: ignore ToolTip events
        """
        jeditor_logger.info(f"EditorMain event: {event}")
        if event.type() == QEvent.Type.ToolTip:
            event.ignore()
            return False
        else:
            return super().event(event)

    def close_tab(self, index: int):
        """
        關閉指定索引的分頁
        Close tab at given index
        """
        widget = self.tab_widget.widget(index)
        if widget:
            widget.close()
        self.tab_widget.removeTab(index)

    @classmethod
    def debug_close(cls):
        """
        除錯模式下自動關閉程式
        Auto-close the program in debug mode
        """
        sys.exit(0)

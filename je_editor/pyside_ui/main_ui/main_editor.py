import os
import pathlib
import queue
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
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QLabel, QMessageBox
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
from je_editor.plugins.plugin_loader import load_external_plugins

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
        self.extend = extend  # 是否為擴充模式（如 PyBreeze）/ Whether in extend mode (e.g. PyBreeze)

        # 確保外部插件已載入（若尚未載入）
        # Ensure external plugins are loaded (if not already)
        load_external_plugins()

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
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self._prev_editor_widget = None  # 追蹤前一個分頁 / Track previous tab for signal disconnect

        # 計時器會在後面初始化並連接 redirect
        # Timer will be initialized later with redirect connection
        self.redirect_timer = None

        # 設定視窗標題與提示
        # Set window title and tooltip
        self.setWindowTitle(language_wrapper.language_word_dict.get("application_name"))
        self.setToolTip(language_wrapper.language_word_dict.get("application_name"))

        # 設定選單列
        # Set menu bar
        set_menu_bar(self)

        # 設定工具列
        # Set toolbar
        from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import build_toolbar
        build_toolbar(self)

        # 設定狀態列 (行/列位置、編碼、行尾)
        # Setup status bar (line/column, encoding, line ending)
        self._line_ending_label = QLabel("LF")
        self._encoding_label = QLabel("UTF-8")
        self._cursor_pos_label = QLabel("Ln 1, Col 1")
        self.statusBar().addPermanentWidget(self._line_ending_label)
        self.statusBar().addPermanentWidget(self._encoding_label)
        self.statusBar().addPermanentWidget(self._cursor_pos_label)

        # 設定應用程式圖示
        # Set application icon
        if not extend:
            self.icon_path = Path(os.getcwd()) / "editor.ico"
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
        self.redirect_timer.setInterval(50)
        self.redirect_timer.timeout.connect(self.redirect)
        self.redirect_timer.start()

        # 定期儲存設定 (每 60 秒)，避免 crash 遺失設定
        # Periodic settings save (every 60s) to prevent data loss on crash
        self._settings_save_timer = QTimer(self)
        self._settings_save_timer.setInterval(60000)
        self._settings_save_timer.timeout.connect(self._periodic_save_settings)
        self._settings_save_timer.start()

        # 建立主要分頁：編輯器與瀏覽器
        # Create main tabs: editor and browser
        self.tab_widget.addTab(EditorWidget(self), language_wrapper.language_word_dict.get("tab_name_editor"))

        # 在非 debug 模式下建立瀏覽器分頁 (QWebEngine 在 CI 無頭環境下可能無法初始化)
        # Only create browser tabs in non-debug mode (QWebEngine may fail in headless CI)
        if not self.debug_mode:
            main_browser_widget = MainBrowserWidget()
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
        # 快速退出：佇列為空時不做任何事 / Early return if queues are empty
        has_stdout = not redirect_manager_instance.std_out_queue.empty()
        has_stderr = not redirect_manager_instance.std_err_queue.empty()
        if not has_stdout and not has_stderr:
            return

        # 直接取得當前活躍的 widget / Get current active widget directly
        widget = self.tab_widget.currentWidget()
        if not isinstance(widget, EditorWidget):
            # 如果當前不是 EditorWidget，找第一個 / Fallback to first EditorWidget
            for i in range(self.tab_widget.count()):
                w = self.tab_widget.widget(i)
                if isinstance(w, EditorWidget):
                    widget = w
                    break
            else:
                return

        text_cursor = widget.code_result.textCursor()

        # 批次處理 stdout / Batch-drain stdout
        if has_stdout:
            stdout_parts = []
            try:
                while not redirect_manager_instance.std_out_queue.empty():
                    msg = str(redirect_manager_instance.std_out_queue.get_nowait()).strip()
                    if msg:
                        stdout_parts.append(msg)
            except queue.Empty:
                pass
            if stdout_parts:
                text_format = QTextCharFormat()
                text_format.setForeground(actually_color_dict.get("normal_output_color"))
                text_cursor.insertText("\n".join(stdout_parts), text_format)
                text_cursor.insertBlock()

        # 批次處理 stderr / Batch-drain stderr
        if has_stderr:
            stderr_parts = []
            try:
                while not redirect_manager_instance.std_err_queue.empty():
                    msg = str(redirect_manager_instance.std_err_queue.get_nowait()).strip()
                    if msg:
                        stderr_parts.append(msg)
            except queue.Empty:
                pass
            if stderr_parts:
                text_format = QTextCharFormat()
                text_format.setForeground(actually_color_dict.get("error_output_color"))
                text_cursor.insertText("\n".join(stderr_parts), text_format)
                text_cursor.insertBlock()

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
        last_file_loaded = False
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

                # 只在第一個 EditorWidget 開啟上次編輯的檔案
                # Only open last file in the first EditorWidget
                if not last_file_loaded:
                    last_file = user_setting_dict.get("last_file", None)
                    if last_file is not None:
                        last_file_path = pathlib.Path(last_file)
                        if last_file_path.is_file() and last_file_path.exists() and widget.code_save_thread is None:
                            init_new_auto_save_thread(str(last_file_path), widget)
                            result = read_file(widget.current_file)
                            if result is not None:
                                widget.code_edit.setPlainText(result[1])
                                widget.code_edit.current_file = widget.current_file
                                widget.code_edit.reset_highlighter()
                                file_is_open_manager_dict.update({str(last_file_path): str(last_file_path)})
                                widget.rename_self_tab()
                                last_file_loaded = True

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
            if widget is not None:
                self.tab_widget.setCurrentWidget(widget)

    def _on_tab_changed(self, index: int) -> None:
        """
        分頁切換時，斷開前一個分頁的信號，連接新分頁的游標位置更新
        Disconnect previous tab's signal, connect new tab's cursor position updates
        """
        # 斷開前一個 EditorWidget 的信號 / Disconnect previous EditorWidget's signal
        if self._prev_editor_widget is not None:
            try:
                self._prev_editor_widget.code_edit.cursorPositionChanged.disconnect(self._update_cursor_pos)
            except RuntimeError:
                pass
            self._prev_editor_widget = None

        widget = self.tab_widget.widget(index)
        if isinstance(widget, EditorWidget):
            widget.code_edit.cursorPositionChanged.connect(self._update_cursor_pos)
            self._prev_editor_widget = widget
            self._update_cursor_pos()
            self._update_encoding_label()
            self._update_line_ending_label(widget)

    def _update_cursor_pos(self) -> None:
        """
        更新狀態列的行/列位置
        Update status bar line/column display
        """
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            cursor = widget.code_edit.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.positionInBlock() + 1
            self._cursor_pos_label.setText(f"Ln {line}, Col {col}")

    def _update_encoding_label(self) -> None:
        """
        更新狀態列的編碼顯示
        Update status bar encoding display
        """
        encoding = user_setting_dict.get("encoding", "utf-8").upper()
        self._encoding_label.setText(encoding)

    def _update_line_ending_label(self, widget: EditorWidget) -> None:
        """
        偵測並更新行尾格式 (CRLF/LF/CR)
        Detect and update line ending format
        """
        if widget.current_file is not None:
            try:
                with open(widget.current_file, "rb") as f:
                    raw = f.read(8192)
                if b"\r\n" in raw:
                    self._line_ending_label.setText("CRLF")
                elif b"\r" in raw:
                    self._line_ending_label.setText("CR")
                else:
                    self._line_ending_label.setText("LF")
            except (OSError, TypeError):
                self._line_ending_label.setText("LF")
        else:
            self._line_ending_label.setText("LF")

    def _periodic_save_settings(self) -> None:
        """
        定期儲存使用者設定，避免 crash 遺失
        Periodically save user settings to prevent data loss
        """
        try:
            write_user_setting()
            write_user_color_setting()
        except Exception as e:
            jeditor_logger.warning(f"Periodic settings save failed: {e}")

    def closeEvent(self, event) -> None:
        """
        視窗關閉事件：儲存使用者設定
        Window close event: save user settings
        """
        jeditor_logger.info("EditorMain closeEvent")
        if hasattr(self, '_settings_save_timer'):
            self._settings_save_timer.stop()
        write_user_setting()
        write_user_color_setting()
        super().closeEvent(event)

    def event(self, event: QEvent) -> bool:
        """
        事件處理：忽略 ToolTip 類型事件
        Event handler: ignore ToolTip events
        """
        if event.type() == QEvent.Type.ToolTip:
            event.ignore()
            return False
        else:
            return super().event(event)

    def close_tab(self, index: int):
        """
        關閉指定索引的分頁，若有未儲存的修改則提示使用者
        Close tab at given index, prompt if unsaved changes
        """
        widget = self.tab_widget.widget(index)
        if widget and isinstance(widget, EditorWidget) and widget._is_modified:
            file_name = widget.current_file or language_wrapper.language_word_dict.get("tab_menu_editor_tab_name")
            reply = QMessageBox.question(
                self,
                language_wrapper.language_word_dict.get("close_tab_unsaved_title"),
                language_wrapper.language_word_dict.get("close_tab_unsaved_message").format(file=file_name),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path
                if not choose_file_get_save_file_path(self):
                    return  # 使用者取消儲存 / User cancelled save
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

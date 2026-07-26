import os
import pathlib
import queue
import sys
from pathlib import Path
from typing import Any, Dict, Type

# 匯入 Jedi 設定，用於 Python 自動補全與分析
# Import Jedi settings for Python auto-completion and analysis
import jedi.settings
# 匯入 PySide6 (Qt for Python) 的核心模組
# Import PySide6 core modules
from PySide6.QtCore import QTimer, QEvent
from PySide6.QtGui import QCloseEvent, QFontDatabase, QIcon, Qt, QTextCharFormat
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QLabel, QMessageBox
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
    apply_theme_colors,
    write_user_color_setting,
    read_user_color_setting,
    actually_color_dict
)
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import (
    user_setting_dict,
    read_user_setting,
    write_user_setting
)
from je_editor.pyside_ui.main_ui.system_tray.extend_system_tray import ExtendSystemTray
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.session.editor_state import editor_state, restore_editor_state
from je_editor.utils.status.status_text import (
    PLAIN_TEXT, cursor_position, encoding_name, language_name, line_ending_display
)
from je_editor.utils.session.open_files_session import (
    SESSION_SETTING_KEY,
    SESSION_STATE_KEY,
    collect_file_states,
    collect_open_files,
    restorable_file_state,
    restorable_files,
)
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

    # 類別層級預設值：擴充模式的子類別（如 PyBreeze）也一定讀得到
    # Class-level default so subclasses in extend mode (e.g. PyBreeze) always see it
    _session_restored = False

    def __init__(self, debug_mode: bool = False, show_system_tray_ray: bool = False, extend: bool = False) -> None:
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
        self._session_restored = False  # 分頁只還原一次 / Restore tabs only once per window

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

        # 設定狀態列 (語言、行尾、編碼、行/列位置)
        # Setup status bar (language, line ending, encoding, line/column)
        self._language_label = QLabel(PLAIN_TEXT)
        self._line_ending_label = QLabel("LF")
        self._encoding_label = QLabel("UTF-8")
        self._cursor_pos_label = QLabel("Ln 1, Col 1")
        self.statusBar().addPermanentWidget(self._language_label)
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

    def clear_code_result(self) -> None:
        """
        清除目前編輯器的輸出結果
        Clear the current editor's output result
        """
        jeditor_logger.info("EditorMain clear_code_result")
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            widget.code_result.clear()

    def _first_editor_widget(self) -> EditorWidget | None:
        """取得第一個 EditorWidget 分頁 / Return the first EditorWidget tab (if any)."""
        for i in range(self.tab_widget.count()):
            w = self.tab_widget.widget(i)
            if isinstance(w, EditorWidget):
                return w
        return None

    @staticmethod
    def _drain_queue(q: "queue.Queue") -> list[str]:
        """將佇列中的非空字串全部取出 / Drain non-empty strings from a queue."""
        parts: list[str] = []
        try:
            while not q.empty():
                msg = str(q.get_nowait()).strip()
                if msg:
                    parts.append(msg)
        except queue.Empty:
            pass
        return parts

    @staticmethod
    def _append_coloured_output(text_cursor: Any, parts: list[str], color_key: str) -> None:
        """將訊息加上顏色後寫入文字游標 / Write messages with the configured colour."""
        if not parts:
            return
        text_format = QTextCharFormat()
        text_format.setForeground(actually_color_dict.get(color_key))
        text_cursor.insertText("\n".join(parts), text_format)
        text_cursor.insertBlock()

    def redirect(self) -> None:
        """將 stdout/stderr 的訊息導入到編輯器的輸出區域 / Redirect stdout/stderr to the output area."""
        has_stdout = not redirect_manager_instance.std_out_queue.empty()
        has_stderr = not redirect_manager_instance.std_err_queue.empty()
        if not has_stdout and not has_stderr:
            return

        widget = self.tab_widget.currentWidget()
        if not isinstance(widget, EditorWidget):
            widget = self._first_editor_widget()
            if widget is None:
                return

        text_cursor = widget.code_result.textCursor()
        if has_stdout:
            self._append_coloured_output(
                text_cursor, self._drain_queue(redirect_manager_instance.std_out_queue),
                "normal_output_color")
        if has_stderr:
            self._append_coloured_output(
                text_cursor, self._drain_queue(redirect_manager_instance.std_err_queue),
                "error_output_color")

    @staticmethod
    def _apply_editor_fonts(widget: EditorWidget) -> None:
        """對單一 EditorWidget 套用程式/輸出區字型 / Apply font styles on an editor widget."""
        style = (
            f"font-size: {user_setting_dict.get('font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('font', 'Lato')};"
        )
        widget.code_edit.setStyleSheet(style)
        widget.code_result.setStyleSheet(style)

    def _try_restore_last_file(self, widget: EditorWidget) -> bool:
        """嘗試載入上次開啟的檔案；若成功則回傳 True / Restore last opened file into the widget."""
        last_file = user_setting_dict.get("last_file", None)
        if last_file is None:
            return False
        last_file_path = pathlib.Path(last_file)
        if not (last_file_path.is_file() and last_file_path.exists() and widget.code_save_thread is None):
            return False
        init_new_auto_save_thread(str(last_file_path), widget)
        result = read_file(widget.current_file)
        if result is None:
            return False
        widget.code_edit.setPlainText(result[1])
        widget.code_edit.current_file = widget.current_file
        widget.code_edit.reset_highlighter()
        file_is_open_manager_dict.update({str(last_file_path): str(last_file_path)})
        widget.rename_self_tab()
        return True

    def startup_setting(self) -> None:
        """啟動時套用使用者設定 / Apply user settings on startup."""
        jeditor_logger.info("EditorMain startup_setting")
        self.setStyleSheet(
            f"font-size: {user_setting_dict.get('ui_font_size', 12)}pt;"
            f"font-family: {user_setting_dict.get('ui_font', 'Lato')};"
        )

        last_file_loaded = False
        for code_editor_count in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(code_editor_count)
            if not isinstance(widget, EditorWidget):
                continue
            self._apply_editor_fonts(widget)
            self.python_compiler = user_setting_dict.get("python_compiler", None)
            if not last_file_loaded:
                last_file_loaded = self._try_restore_last_file(widget)

        self._restore_open_files_session()

        app = QApplication.instance()
        style_name = user_setting_dict.get("ui_style", "dark_amber.xml")
        if app is not None:
            self.apply_stylesheet(app, style_name)
        # 顏色跟著樣式走：淺色樣式要用淺色底調出來的那一組
        # The colours follow the style: a light one needs the light set
        apply_theme_colors(style_name)

    def _open_file_paths(self) -> list[str]:
        """取得所有分頁目前開啟的檔案 / Every tab's currently open file."""
        return [
            self.tab_widget.widget(index).current_file
            for index in range(self.tab_widget.count())
            if isinstance(self.tab_widget.widget(index), EditorWidget)
        ]

    def _restore_open_files_session(self) -> None:
        """
        還原上次關閉時開啟的分頁
        Reopen the tabs that were open at the last shutdown.

        只在每個視窗執行一次：``startup_setting`` 也會在開啟資料夾時被呼叫，
        若不設旗標，使用者關掉的分頁會在開啟資料夾後又冒出來。
        Runs once per window: ``startup_setting`` is also called when opening a
        folder, and without this flag a tab the user closed would come back.

        整段以 try/except 包住：損毀或被手動編輯的設定檔絕不能擋住編輯器啟動。
        The whole step is guarded: a corrupt or hand-edited settings file must
        never stop the editor from starting.
        """
        if self._session_restored or not user_setting_dict.get("restore_session", True):
            return
        self._session_restored = True
        try:
            to_restore = restorable_files(
                user_setting_dict.get(SESSION_SETTING_KEY),
                already_open=[path for path in self._open_file_paths() if path],
            )
            stored_states = user_setting_dict.get(SESSION_STATE_KEY)
            for file_path in to_restore:
                self.go_to_new_tab(Path(file_path))
                restore_editor_state(
                    self.tab_widget.currentWidget(),
                    restorable_file_state(stored_states, file_path))
        except Exception as error:
            jeditor_logger.warning(f"Restoring the open-file session failed: {error}")

    def _save_open_files_session(self) -> None:
        """
        記錄目前開啟的分頁與其編輯狀態，供下次啟動還原
        Record the open tabs and their editor state so the next startup can
        restore both.
        """
        try:
            user_setting_dict[SESSION_SETTING_KEY] = collect_open_files(self._open_file_paths())
            user_setting_dict[SESSION_STATE_KEY] = collect_file_states(
                self._open_file_states())
        except Exception as error:
            jeditor_logger.warning(f"Saving the open-file session failed: {error}")

    def _open_file_states(self) -> dict:
        """
        取得每個編輯分頁目前的游標、書籤與折疊狀態
        Collect each editor tab's caret, bookmarks and folds.

        :return: 路徑對應狀態 / path -> state
        """
        from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
        states: dict = {}
        for index in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(index)
            if not isinstance(widget, EditorWidget) or not widget.current_file:
                continue
            states[str(widget.current_file)] = editor_state(widget)
        return states

    def go_to_new_tab(self, file_path: Path) -> None:
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
        self.refresh_status_bar()

    def _update_cursor_pos(self) -> None:
        """
        更新狀態列的行/列位置
        Update status bar line/column display
        """
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, EditorWidget):
            cursor = widget.code_edit.textCursor()
            self._cursor_pos_label.setText(cursor_position(
                cursor.blockNumber() + 1, cursor.positionInBlock() + 1))

    def refresh_status_bar(self) -> None:
        """
        依目前分頁重畫狀態列
        Redraw the status bar from the current tab.

        顯示的是這個分頁記憶中的狀態，而不是全域設定或磁碟上的內容：使用者從選單
        改過編碼或行尾之後，狀態列要跟著改，而不是繼續顯示檔案原本的樣子。改完
        設定的地方要呼叫這個方法。
        What it shows is the tab's own state, not the global setting or what is on
        disk: after the user changes the encoding or line ending from the menu the
        status bar has to follow, rather than keep describing the file as it was
        opened. Whatever changes those settings calls this.
        """
        widget = self.tab_widget.currentWidget()
        if not isinstance(widget, EditorWidget):
            self._language_label.setText(PLAIN_TEXT)
            self._line_ending_label.setText(line_ending_display(None))
            self._encoding_label.setText(encoding_name(None))
            self._cursor_pos_label.setText(cursor_position(1, 1))
            return
        self._language_label.setText(language_name(widget.current_file))
        self._line_ending_label.setText(
            line_ending_display(getattr(widget, "line_ending", None)))
        self._encoding_label.setText(
            encoding_name(getattr(widget, "file_encoding", None)))
        self._update_cursor_pos()

    def _periodic_save_settings(self) -> None:
        """
        定期儲存使用者設定，避免 crash 遺失
        Periodically save user settings to prevent data loss
        """
        try:
            self._save_open_files_session()
            write_user_setting()
            write_user_color_setting()
        except Exception as e:
            jeditor_logger.warning(f"Periodic settings save failed: {e}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        視窗關閉事件：關閉所有分頁並儲存使用者設定
        Window close event: close all tabs and save user settings
        """
        jeditor_logger.info("EditorMain closeEvent")
        if hasattr(self, '_settings_save_timer'):
            self._settings_save_timer.stop()
        # 必須在關閉分頁前記錄，否則分頁已消失就抓不到開啟中的檔案
        # Must run before the tabs close, or the open files are already gone
        self._save_open_files_session()
        # 關閉所有編輯器分頁（停止自動儲存和檔案監控）
        # Close all editor tabs (stop auto-save and file watchers)
        for i in range(self.tab_widget.count() - 1, -1, -1):
            widget = self.tab_widget.widget(i)
            if widget and isinstance(widget, EditorWidget):
                widget.close()
        # 工具列的背景工作也要收掉：視窗銷毀時它們還在跑的話 Qt 會中止整個程序
        # The toolbar's background work goes too: Qt aborts the process if one of
        # those is still running when the window is destroyed
        from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
            stop_background_threads
        )
        stop_background_threads()
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

    def close_tab(self, index: int) -> None:
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

    @staticmethod
    def debug_close() -> None:
        """
        除錯模式下自動關閉程式
        Auto-close the program in debug mode
        """
        app = QApplication.instance()
        if app is not None:
            app.quit()

from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.utils.logging.loggin_instance import jeditor_logger

# 啟用未來註解功能，允許型別提示使用字串前向參照
# Enable future annotations, allowing forward references in type hints

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴
    # Import EditorMain only for type checking

import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class ExtendSystemTray(QSystemTrayIcon):
    """
    擴充系統匣功能，提供隱藏、最大化、還原、關閉等操作
    Extend system tray functionality with hide, maximize, restore, and close actions
    """

    def __init__(self, main_window: EditorMain):
        # 初始化並記錄日誌
        # Initialize and log
        jeditor_logger.info(f"Init ExtendSystemTray main_window: {main_window}")
        super().__init__(parent=main_window)

        # 建立右鍵選單
        # Create context menu
        self.menu = QMenu()
        self.main_window = main_window

        # === 隱藏主視窗 / Hide main window ===
        self.hide_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_hide"))
        self.hide_main_window_action.triggered.connect(self.main_window.hide)
        self.menu.addAction(self.hide_main_window_action)

        # === 最大化主視窗 / Maximize main window ===
        self.maximized_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_maximized"))
        self.maximized_main_window_action.triggered.connect(self.main_window.showMaximized)
        self.menu.addAction(self.maximized_main_window_action)

        # === 還原主視窗 / Restore main window ===
        self.normal_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_normal"))
        self.normal_main_window_action.triggered.connect(self.main_window.showNormal)
        self.menu.addAction(self.normal_main_window_action)

        # === 關閉應用程式 / Close application ===
        self.close_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_close"))
        self.close_main_window_action.triggered.connect(self.close_all)
        self.menu.addAction(self.close_main_window_action)

        # 設定選單到系統匣圖示
        # Attach menu to system tray icon
        self.setContextMenu(self.menu)

        # 綁定點擊事件 (例如雙擊)
        # Connect click events (e.g., double-click)
        self.activated.connect(self.clicked)

    def close_all(self):
        """
        關閉應用程式：隱藏圖示、關閉主視窗並結束程式
        Close the application: hide tray icon, close main window, and exit program
        """
        jeditor_logger.info("ExtendSystemTray close_all")
        self.setVisible(False)
        self.main_window.close()
        sys.exit(0)

    def clicked(self, reason):
        """
        處理系統匣點擊事件
        Handle system tray click events
        """
        if reason == self.ActivationReason.DoubleClick:
            # 如果是雙擊，最大化主視窗
            # If double-click, maximize the main window
            jeditor_logger.info("ExtendSystemTray DoubleClick")
            self.main_window.showMaximized()

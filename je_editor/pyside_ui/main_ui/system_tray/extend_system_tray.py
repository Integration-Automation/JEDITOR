from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
import sys

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class ExtendSystemTray(QSystemTrayIcon):

    def __init__(self, main_window: EditorMain):
        super().__init__(parent=main_window)
        self.menu = QMenu()
        self.main_window = main_window
        self.hide_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_hide"))
        self.hide_main_window_action.triggered.connect(self.main_window.hide)
        self.menu.addAction(self.hide_main_window_action)
        self.maximized_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_maximized"))
        self.maximized_main_window_action.triggered.connect(self.main_window.showMaximized)
        self.menu.addAction(self.maximized_main_window_action)
        self.normal_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_normal"))
        self.normal_main_window_action.triggered.connect(self.main_window.showNormal)
        self.menu.addAction(self.normal_main_window_action)
        self.close_main_window_action = QAction(
            language_wrapper.language_word_dict.get("system_tray_close"))
        self.close_main_window_action.triggered.connect(self.close_all)
        self.menu.addAction(self.close_main_window_action)
        self.setContextMenu(self.menu)
        self.activated.connect(self.clicked)

    def close_all(self):
        self.setVisible(False)
        self.main_window.close()
        sys.exit(0)

    def clicked(self, reason):
        if reason == self.ActivationReason.DoubleClick:
            self.main_window.showMaximized()

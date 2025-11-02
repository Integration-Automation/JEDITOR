from __future__ import annotations

from typing import TYPE_CHECKING

# 匯入各種子選單的建構函式
# Import functions to build different sub-menus
from je_editor.pyside_ui.main_ui.menu.dock_menu.build_dock_menu import set_dock_menu
from je_editor.pyside_ui.main_ui.menu.language_menu.build_language_server import set_language_menu
from je_editor.pyside_ui.main_ui.menu.style_menu.build_style_menu import set_style_menu
from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_menu import set_tab_menu
from je_editor.pyside_ui.main_ui.menu.text_menu.build_text_menu import set_text_menu
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 啟用未來註解功能，允許型別提示使用字串前向參照
# Enable future annotations, allowing forward references in type hints
# TYPE_CHECKING 用於避免在執行時載入不必要的模組
# TYPE_CHECKING prevents unnecessary imports at runtime

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴
    # Import EditorMain only for type checking

from PySide6.QtWidgets import QMenuBar
# 匯入 QMenuBar，用於建立選單列
# Import QMenuBar to create the menu bar

# 其他子選單建構函式
# Other sub-menu builders
from je_editor.pyside_ui.main_ui.menu.check_style_menu.build_check_style_menu import set_check_menu
from je_editor.pyside_ui.main_ui.menu.file_menu.build_file_menu import set_file_menu
from je_editor.pyside_ui.main_ui.menu.help_menu.build_help_menu import set_help_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.build_run_menu import set_run_menu
from je_editor.pyside_ui.main_ui.menu.python_env_menu.build_venv_menu import set_venv_menu


def set_menu_bar(ui_we_want_to_set: EditorMain) -> None:
    """
    建立主選單列，並依序加入各種子選單
    Build the main menu bar and add all sub-menus in order
    """
    jeditor_logger.info(f"set_menu_bar.py set_menu_bar ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立一個新的選單列
    # Create a new menu bar
    ui_we_want_to_set.menu = QMenuBar()

    # === 加入各種子選單 ===
    # === Add different sub-menus ===
    set_file_menu(ui_we_want_to_set)  # 檔案選單 / File menu
    set_run_menu(ui_we_want_to_set)  # 執行選單 / Run menu
    set_text_menu(ui_we_want_to_set)  # 文字設定選單 / Text menu
    set_check_menu(ui_we_want_to_set)  # 程式碼檢查選單 / Code style check menu
    set_help_menu(ui_we_want_to_set)  # 幫助選單 / Help menu
    set_venv_menu(ui_we_want_to_set)  # Python 虛擬環境選單 / Python venv menu
    set_tab_menu(ui_we_want_to_set)  # 分頁選單 / Tab menu
    set_dock_menu(ui_we_want_to_set)  # Dock 視窗選單 / Dock menu
    set_style_menu(ui_we_want_to_set)  # 介面樣式選單 / Style menu
    set_language_menu(ui_we_want_to_set)  # 語言選單 / Language menu

    # 將選單列設定到主視窗
    # Attach the menu bar to the main editor window
    ui_we_want_to_set.setMenuBar(ui_we_want_to_set.menu)

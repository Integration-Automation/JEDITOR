# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入內建瀏覽器元件，用於在程式內開啟網頁
# Import embedded browser widget for opening web pages inside the app
from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入 Qt 動作與訊息框
# Import QAction and QMessageBox from PySide6
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定「說明」選單 (Help Menu)
# Set up the Help menu
def set_help_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_help_menu.py set_help_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立 Help 選單
    # Create Help menu
    ui_we_want_to_set.help_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("help_menu_label"))

    # 建立「開啟 GitHub」動作
    # Add "Open GitHub" action
    ui_we_want_to_set.help_menu.help_github_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_github_label"))
    ui_we_want_to_set.help_menu.help_github_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://github.com/Integrated-Testing-Environment/je_editor",
            language_wrapper.language_word_dict.get("help_menu_open_github_label"))
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_github_action)

    # 建立「開啟文件」動作
    # Add "Open Documentation" action
    ui_we_want_to_set.help_menu.help_doc_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_doc_label"))
    ui_we_want_to_set.help_menu.help_doc_action.triggered.connect(
        lambda: open_web_browser(
            ui_we_want_to_set,
            "https://je-editor.readthedocs.io/en/latest/",
            language_wrapper.language_word_dict.get("help_menu_open_doc_label"))
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_doc_action)

    # 建立「關於」動作
    # Add "About" action
    ui_we_want_to_set.help_menu.help_about_action = QAction(
        language_wrapper.language_word_dict.get("help_menu_open_about_label"))
    ui_we_want_to_set.help_menu.help_about_action.triggered.connect(
        show_about
    )
    ui_we_want_to_set.help_menu.addAction(ui_we_want_to_set.help_menu.help_about_action)


# 開啟內建瀏覽器分頁
# Open a new tab in the embedded browser
def open_web_browser(ui_we_want_to_set: EditorMain, url: str, tab_name: str):
    jeditor_logger.info("build_help_menu.py open_web_browser "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"url: {url} "
                        f"tab_name: {tab_name}")
    ui_we_want_to_set.tab_widget.addTab(
        MainBrowserWidget(start_url=url),  # 建立瀏覽器元件並載入指定 URL
        f"{tab_name}{ui_we_want_to_set.tab_widget.count()}"  # 分頁名稱 + 當前分頁數
    )


# 顯示「關於」訊息框
# Show "About" message box
def show_about():
    jeditor_logger.info("build_help_menu.py show_about")
    message_box = QMessageBox()
    message_box.setText(
        """
JEditor
Create by JE-Chen 2020 ~ Now
        """
    )
    message_box.exec()
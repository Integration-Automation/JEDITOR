# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入 Qt 動作與訊息框
# Import QAction and QMessageBox from PySide6
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

# 匯入使用者設定字典，用來保存語言設定
# Import user settings dictionary for saving language preferences
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定語言選單
# Set up the Language menu
def set_language_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_language_server.py set_language_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立 Language 選單
    # Create Language menu
    ui_we_want_to_set.language_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("language_menu_label")
    )

    # 建立「切換到英文」動作
    # Add "Switch to English" action
    ui_we_want_to_set.language_menu.change_to_english_language_action = QAction(
        language_wrapper.language_word_dict.get("language_menu_bar_english")
    )
    ui_we_want_to_set.language_menu.change_to_english_language_action.triggered.connect(
        lambda: set_language("English", ui_we_want_to_set)
    )

    # 建立「切換到繁體中文」動作
    # Add "Switch to Traditional Chinese" action
    ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action = QAction(
        language_wrapper.language_word_dict.get("language_menu_bar_traditional_chinese")
    )
    ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action.triggered.connect(
        lambda: set_language("Traditional_Chinese", ui_we_want_to_set)
    )

    # 將動作加入選單
    # Add actions to the menu
    ui_we_want_to_set.language_menu.addAction(
        ui_we_want_to_set.language_menu.change_to_english_language_action
    )
    ui_we_want_to_set.language_menu.addAction(
        ui_we_want_to_set.language_menu.change_to_traditional_chinese_language_action
    )


# 設定語言
# Set the application language
def set_language(language: str, ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_language_server.py set_language "
                        f"language: {language} "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")

    # 重設語言 (更新多語言字典)
    # Reset language (update multi-language dictionary)
    language_wrapper.reset_language(language)

    # 更新使用者設定，保存語言偏好
    # Update user settings dictionary to persist language preference
    user_setting_dict.update({"language": language})

    # 顯示提示訊息，提醒使用者需要重新啟動程式
    # Show a message box to remind user to restart the application
    message_box = QMessageBox(ui_we_want_to_set)
    message_box.setText(language_wrapper.language_word_dict.get("language_menu_bar_please_restart_messagebox"))
    message_box.show()
from __future__ import annotations

from typing import TYPE_CHECKING

# 匯入 Qt 訊息框
# Import QMessageBox for showing message dialogs
from PySide6.QtWidgets import QMessageBox

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger
# 匯入多語言包裝器，用於多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


# 顯示「請先關閉目前執行中的程式」訊息框
# Show a message box: "Please stop the currently running program first"
def please_close_current_running_messagebox(ui_we_want_to_set: EditorMain):
    # 紀錄日誌，方便除錯
    # Log info for debugging
    jeditor_logger.info(f"utils.py please_close_current_running_messagebox ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立訊息框，父視窗為主編輯器
    # Create a message box with the main editor as parent
    please_stop_current_running_program_messagebox = QMessageBox(ui_we_want_to_set)

    # 設定訊息框文字，從多語言字典取得對應語言的提示
    # Set message text, retrieved from multi-language dictionary
    please_stop_current_running_program_messagebox.setText(
        language_wrapper.language_word_dict.get("please_stop_current_running_program")
    )

    # 顯示訊息框
    # Show the message box
    please_stop_current_running_program_messagebox.show()

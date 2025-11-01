from __future__ import annotations

from typing import TYPE_CHECKING

from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環匯入問題
    # Import only for type checking, prevents circular imports
    from je_editor.pyside_ui.main_ui.main_editor import EditorWidget

from je_editor.pyside_ui.code.auto_save.auto_save_thread import CodeEditSaveThread

# --- 全域管理字典 / Global manager dictionaries ---

# 管理每個檔案對應的自動儲存執行緒
# Manage auto-save threads for each file
auto_save_manager_dict: dict = dict()

# 管理檔案是否已經開啟
# Track whether a file is currently open
file_is_open_manager_dict: dict = dict()


def init_new_auto_save_thread(file_path: str, widget: EditorWidget):
    """
    初始化新的自動儲存執行緒
    Initialize a new auto-save thread for the given file and editor widget.

    :param file_path: 檔案路徑 / Path of the file to be auto-saved
    :param widget: 編輯器元件 / Editor widget instance
    """
    # 記錄初始化訊息 (方便除錯)
    # Log initialization info (for debugging)
    jeditor_logger.info(f"auto_save_manager.py init_new_auto_save_thread "
                        f"file_path: {file_path} "
                        f"widget: {widget}")

    # 將目前編輯器綁定的檔案設為 file_path
    # Set the current file of the editor widget
    widget.current_file = file_path

    # 如果該檔案尚未有自動儲存執行緒
    # If no auto-save thread exists for this file
    if auto_save_manager_dict.get(file_path, None) is None:
        # 建立新的自動儲存執行緒，綁定到編輯器
        # Create a new auto-save thread for this file
        widget.code_save_thread = CodeEditSaveThread(
            file_to_save=widget.current_file, editor=widget.code_edit
        )

        # 更新管理字典，記錄該檔案對應的執行緒
        # Update manager dict with the new thread
        auto_save_manager_dict.update({
            file_path: widget.code_save_thread
        })

        # 啟動自動儲存執行緒
        # Start the auto-save thread
        widget.code_save_thread.start()
from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save.auto_save_manager import file_is_open_manager_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.save.save_file import write_file


def choose_file_get_save_file_path(parent_qt_instance: EditorMain) -> bool:
    """
    開啟「另存新檔」對話框，將編輯器內容儲存到檔案
    Open "Save As" dialog and save editor content to file
    :param parent_qt_instance: Pyside 主視窗 / Pyside parent
    :return: 是否成功儲存檔案 / whether file was saved successfully
    """
    jeditor_logger.info("save_file_dialog.py choose_file_get_save_file_path"
                        f" parent_qt_instance: {parent_qt_instance}")

    # 取得目前分頁的編輯器元件
    # Get current tab's editor widget
    widget = parent_qt_instance.tab_widget.currentWidget()

    if isinstance(widget, EditorWidget):
        # 開啟檔案儲存對話框 / Open file save dialog
        file_path = QFileDialog().getSaveFileName(
            parent=parent_qt_instance,
            dir=os.getcwd(),
            filter="""Python file (*.py);;
            HTML file (*.html);;
            File (*.*)"""
        )[0]

        # 確認使用者有選擇檔案路徑 / Ensure user selected a file path
        if file_path is not None and file_path != "":
            # 更新目前檔案路徑 / Update current file path
            widget.current_file = file_path

            # 將編輯器內容寫入檔案 / Write editor content to file
            write_file(file_path, widget.code_edit.toPlainText())

            # 更新已開啟檔案管理字典 / Update opened file manager dictionary
            path = Path(file_path)
            file_is_open_manager_dict.update({str(path): str(path.name)})

            # 若有自動儲存執行緒，更新其監控的檔案與編輯器
            # If auto-save thread exists, update its file and editor reference
            if widget.code_save_thread is not None:
                widget.code_save_thread.file = file_path
                widget.code_save_thread.editor = widget.code_edit

            # 更新分頁標題 / Update tab title
            widget.rename_self_tab()
            return True
        return False
    return False

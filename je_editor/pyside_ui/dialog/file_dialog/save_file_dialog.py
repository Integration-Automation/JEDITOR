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


def _build_save_file_filters() -> list[str]:
    """
    動態建立檔案儲存對話框的篩選器列表，包含 Python 與所有插件語言。
    Dynamically build file filter list for save dialog, including Python and all plugin languages.
    """
    from je_editor.plugins import get_all_plugin_run_configs

    # 預設篩選器 / Default filters
    filters = ["Python file (*.py)"]

    # 從插件執行設定收集篩選器 / Collect filters from plugin run configs
    for config in get_all_plugin_run_configs():
        name = config.get("name", "")
        suffixes = config.get("suffixes", ())
        if name and suffixes:
            suffix_pattern = " ".join(f"*{s}" for s in suffixes)
            filters.append(f"{name} ({suffix_pattern})")

    # 加入通用篩選器 / Add generic filters
    filters.append("HTML file (*.html)")
    filters.append("File (*.*)")

    return filters


def _select_filter_by_suffix(filters: list[str], suffix: str) -> str:
    """
    根據副檔名自動選擇對應的篩選器。
    Automatically select the matching filter based on file suffix.
    例如 suffix=".cpp" 會匹配含有 "*.cpp" 的篩選器。
    e.g. suffix=".cpp" matches the filter containing "*.cpp".
    """
    if not suffix:
        return filters[0]
    for f in filters:
        if f"*{suffix}" in f:
            return f
    return filters[0]


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
        # 動態建立檔案篩選器（包含插件語言）
        # Dynamically build file filter (including plugin languages)
        filters = _build_save_file_filters()
        file_filter = ";;".join(filters)

        # 根據目前檔案的副檔名自動選擇對應篩選器
        # Auto-select filter based on current file's suffix
        current_suffix = ""
        if widget.current_file:
            current_suffix = Path(widget.current_file).suffix
        selected = _select_filter_by_suffix(filters, current_suffix)

        # 開啟檔案儲存對話框 / Open file save dialog
        file_path = QFileDialog().getSaveFileName(
            parent=parent_qt_instance,
            dir=os.getcwd(),
            filter=file_filter,
            selectedFilter=selected,
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

            # 更新分頁標題並清除未儲存標記 / Update tab title and clear unsaved marker
            widget.rename_self_tab()
            widget.mark_saved()
            return True
        return False
    return False

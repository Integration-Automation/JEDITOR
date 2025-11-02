from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save.auto_save_manager import init_new_auto_save_thread, file_is_open_manager_dict
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict, read_user_setting
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.venv_check.check_venv import check_and_choose_venv

if TYPE_CHECKING:
    # 僅在型別檢查時匯入，避免循環依賴
    # Only imported during type checking to avoid circular imports
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_file_path(parent_qt_instance: EditorMain) -> None:
    """
    開啟檔案並將內容載入編輯器
    Open file and set code edit content
    :param parent_qt_instance: Pyside 主視窗 / Pyside parent
    :return: None
    """
    jeditor_logger.info("open_file_dialog.py choose_file_get_open_file_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    widget = parent_qt_instance.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        # 開啟檔案選擇對話框 / Open file dialog
        file_path = QFileDialog().getOpenFileName(
            parent=parent_qt_instance,
            dir=str(Path.cwd()),
            filter="""Python file (*.py);;
            HTML file (*.html);;
            File (*.*)"""
        )[0]

        if file_path is not None and file_path != "":
            # 檢查檔案是否已經開啟 / Check if file already opened
            if file_is_open_manager_dict.get(str(Path(file_path)), None) is not None:
                widget.tab_manager.setCurrentWidget(
                    widget.tab_manager.findChild(EditorWidget, str(Path(file_path).name)))
                return
            else:
                # 記錄已開啟檔案 / Register opened file
                file_is_open_manager_dict.update({file_path: str(Path(file_path).name)})

            # 設定目前檔案路徑 / Set current file path
            widget.current_file = file_path
            # 讀取檔案內容 / Read file content
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(file_content)

            # 啟動自動儲存執行緒 / Start auto-save thread
            if widget.current_file is not None and widget.code_save_thread is None:
                init_new_auto_save_thread(widget.current_file, widget)
            else:
                widget.code_save_thread.file = widget.current_file

            # 更新使用者設定中的最後開啟檔案 / Update last opened file in user settings
            user_setting_dict.update({"last_file": str(widget.current_file)})
            # 更新分頁標題 / Rename tab title
            widget.rename_self_tab()


def choose_dir_get_dir_path(parent_qt_instance: EditorMain) -> None:
    """
    選擇資料夾並更新工作目錄與專案樹
    Choose directory and update working dir and project tree
    """
    jeditor_logger.info("open_file_dialog.py choose_dir_get_dir_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    dir_path = QFileDialog().getExistingDirectory(parent=parent_qt_instance, )
    if dir_path != "":
        check_path = Path(dir_path)
    else:
        return

    if check_path.exists() and check_path.is_dir():
        # 更新工作目錄 / Update working directory
        parent_qt_instance.working_dir = dir_path
        os.chdir(dir_path)

        # 更新所有編輯器的專案樹與環境檢查 / Update project tree and check env for all editors
        for code_editor in range(parent_qt_instance.tab_widget.count()):
            widget = parent_qt_instance.tab_widget.widget(code_editor)
            if isinstance(widget, EditorWidget):
                widget.project_treeview.setRootIndex(widget.project_treeview_model.index(dir_path))
                widget.code_edit.check_env()

        # 設定虛擬環境路徑 / Set virtual environment path
        if sys.platform in ["win32", "cygwin", "msys"]:
            venv_path = Path(os.getcwd() + "/venv/Scripts")
        else:
            venv_path = Path(os.getcwd() + "/venv/bin")

        parent_qt_instance.python_compiler = check_and_choose_venv(venv_path)

        # 重新讀取使用者設定並套用啟動設定 / Reload user settings and apply startup settings
        read_user_setting()
        parent_qt_instance.startup_setting()

        # 重設語言設定 / Reset language
        language_wrapper.reset_language(user_setting_dict.get("language", "English"))

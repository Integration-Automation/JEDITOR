from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

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


def _prompt_for_file(parent_qt_instance: EditorMain) -> str:
    """彈出檔案選擇對話框並回傳路徑 (若取消為空字串) / Prompt file dialog; return path or ''."""
    file_path = QFileDialog().getOpenFileName(
        parent=parent_qt_instance,
        dir=str(Path.cwd()),
        filter="""Python file (*.py);;
            HTML file (*.html);;
            File (*.*)"""
    )[0]
    return file_path or ""


def choose_file_get_open_file_path(parent_qt_instance: EditorMain) -> None:
    """
    開啟檔案並將內容載入目前的編輯器分頁
    Open a file and load its content into the editor tab in front.

    交給 ``EditorWidget.open_an_file``：它記下檔案的編碼與行尾、更新檔案監控，
    讀不了時會告訴使用者。以前這裡只用 UTF-8 讀，非 UTF-8 的檔案丟出例外，
    而且檔案已經被記成「已開啟」，之後再也開不了。
    Handed to ``EditorWidget.open_an_file``, which keeps the file's encoding and
    line ending, updates the file watcher and tells the user when the file cannot
    be read. This used to read UTF-8 only: a file in another encoding raised out
    of the menu, already recorded as open, so it could never be opened again.
    """
    jeditor_logger.info("open_file_dialog.py choose_file_get_open_file_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    widget = parent_qt_instance.tab_widget.currentWidget()
    if not isinstance(widget, EditorWidget):
        return

    file_path = _prompt_for_file(parent_qt_instance)
    if not file_path:
        return
    if not widget.open_an_file(Path(file_path)):
        return

    from je_editor.pyside_ui.main_ui.menu.file_menu.build_file_menu import add_to_recent_files
    add_to_recent_files(str(widget.current_file))


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
            venv_path = Path(os.getcwd()) / "venv" / "Scripts"
        else:
            venv_path = Path(os.getcwd()) / "venv" / "bin"

        parent_qt_instance.python_compiler = check_and_choose_venv(venv_path)

        # 重新讀取使用者設定並套用啟動設定 / Reload user settings and apply startup settings
        read_user_setting()
        parent_qt_instance.startup_setting()

        # 重設語言設定 / Reset language
        language_wrapper.reset_language(user_setting_dict.get("language", "English"))

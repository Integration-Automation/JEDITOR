"""
把資料夾加進工作區、從工作區移除
Add a folder to the workspace, and remove one from it.

「開啟資料夾」是換一個專案：工作目錄跟著換，整個工作區換成那個資料夾。這裡做的是
另一件事：在目前的專案旁邊多放一個根目錄，工作目錄不動。
"Open Folder" switches project: the working directory moves and the whole
workspace becomes that folder. This does something else: it puts another root
beside the current project and leaves the working directory alone.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QWidget

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import write_user_setting
from je_editor.pyside_ui.main_ui.workspace.workspace_roots import (
    remember_extra_roots, window_workspace
)
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def add_folder_to_workspace(main_window: QWidget, folder: str | None = None) -> bool:
    """
    把一個資料夾加進工作區
    Add a folder to the workspace.

    :param main_window: 主視窗 / the main window
    :param folder: 要加入的資料夾；沒給時讓使用者挑 / the folder to add, chosen by
        the user when omitted
    :return: 是否真的加入了 / whether a folder was added
    """
    word = language_wrapper.language_word_dict
    if folder is None:
        folder = QFileDialog.getExistingDirectory(
            main_window, word.get("file_menu_add_workspace_folder_label"))
    if not folder or not Path(folder).is_dir():
        return False
    workspace = window_workspace(main_window)
    if not workspace.add_root(folder):
        QMessageBox.information(
            main_window, word.get("file_menu_add_workspace_folder_label"),
            word.get("workspace_folder_already_added"))
        return False
    jeditor_logger.info("workspace: added the folder %s", folder)
    _save_roots(main_window)
    return True


def remove_folder_from_workspace(main_window: QWidget, folder: str | None = None) -> bool:
    """
    把一個另外加入的資料夾從工作區移除
    Remove an added folder from the workspace.

    主要的根目錄就是工作目錄，不能在這裡移除；要換它得用「開啟資料夾」。
    The primary root is the working directory and cannot be removed here;
    changing it is what "Open Folder" is for.

    :param main_window: 主視窗 / the main window
    :param folder: 要移除的資料夾；沒給時讓使用者從清單挑 / the folder to remove,
        picked from a list by the user when omitted
    :return: 是否真的移除了 / whether a folder was removed
    """
    word = language_wrapper.language_word_dict
    title = word.get("file_menu_remove_workspace_folder_label")
    workspace = window_workspace(main_window)
    extra = [root.path for root in workspace.roots[1:] if root.is_local]
    if not extra:
        QMessageBox.information(main_window, title, word.get("workspace_no_extra_folders"))
        return False
    if folder is None:
        folder, accepted = QInputDialog.getItem(
            main_window, title, word.get("workspace_remove_folder_prompt"), extra, 0, False)
        if not accepted:
            return False
    if folder not in extra or not workspace.remove_root(folder):
        return False
    jeditor_logger.info("workspace: removed the folder %s", folder)
    _save_roots(main_window)
    return True


def _save_roots(main_window: QWidget) -> None:
    """
    把工作區的根目錄記進設定並立刻寫檔
    Record the workspace's roots in the settings and write the file at once.

    不等定期存檔：使用者接著就切到別的專案的話，這個專案的根目錄清單就丟了。
    The periodic save is not waited for: were the user to switch project straight
    away, this project's list of roots would be lost.
    """
    remember_extra_roots(window_workspace(main_window))
    write_user_setting()

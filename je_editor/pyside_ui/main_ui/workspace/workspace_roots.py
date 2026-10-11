"""
從視窗取得工作區與它的根目錄
Get the workspace, and its roots, from a window.

問題面板、TODO 面板、測試面板、快速開啟與搜尋原本各自寫了一份「用視窗的工作目錄，
沒有就用目前目錄」。現在都問這裡，所以它們對「專案在哪裡」的答案一定相同，而且
工作區有好幾個根目錄時也都知道。
The problems panel, the TODO panel, the test panel, quick open and search each
used to spell out "the window's working directory, or the current one". They all
ask here now, so their answer to where the project is always agrees, and all of
them learn about it when the workspace has several roots.
"""
from __future__ import annotations

import os
from pathlib import Path

from je_editor.core.services.editor_services import EditorServices
from je_editor.core.workspace.workspace_model import ProjectRoot, Workspace
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

# 使用者設定裡記錄「主要根目錄以外的根目錄」的鍵
# The user-setting key that records the roots beyond the primary one
EXTRA_ROOTS_SETTING = "workspace_roots"


def window_workspace(main_window: object) -> Workspace:
    """
    取得視窗的工作區
    The workspace of a window.

    視窗沒有核心服務（宿主程式自己的視窗、測試用的替身）時，照原本的規則組一個
    只有一個根目錄的工作區：視窗的工作目錄，沒有就用目前目錄。
    A window without core services, a host's own window or a test double, gets a
    single-root workspace built by the old rule: the window's working directory,
    or the current directory when it has none.

    :param main_window: 主視窗 / the main window
    :return: 工作區 / the workspace
    """
    services = getattr(main_window, "services", None)
    if isinstance(services, EditorServices) and services.workspace.roots:
        return services.workspace
    working_dir = getattr(main_window, "working_dir", None)
    if working_dir and Path(str(working_dir)).is_dir():
        return Workspace.single_root(str(working_dir))
    return Workspace.single_root(os.getcwd())


def primary_root_path(main_window: object) -> str:
    """
    取得主要根目錄的路徑，也就是原本的「專案目錄」
    The path of the primary root, which is what the project directory used to be.

    :param main_window: 主視窗 / the main window
    :return: 目錄路徑 / the directory
    """
    return local_root_paths(main_window)[0]


def local_root_paths(main_window: object) -> list[str]:
    """
    取得每個本機根目錄的路徑
    The path of every local root.

    :param main_window: 主視窗 / the main window
    :return: 目錄路徑，至少一個 / the directories, at least one
    """
    paths = [root.path for root in window_workspace(main_window).roots if root.is_local]
    return paths or [os.getcwd()]


def labelled_root_paths(main_window: object) -> list[tuple[str, str]]:
    """
    取得每個本機根目錄的顯示名稱與路徑
    The display name and the path of every local root.

    交給背景執行緒的是這份清單而不是工作區本身，執行緒就不會碰到 UI 執行緒正在改
    的物件。
    A worker thread is handed this list rather than the workspace itself, so it
    never touches an object the UI thread may be changing.

    :param main_window: 主視窗 / the main window
    :return: ``(顯示名稱, 路徑)`` / ``(label, path)``
    """
    return [(label, root.path)
            for label, root in window_workspace(main_window).labelled_roots() if root.is_local]


def restore_extra_roots(workspace: Workspace) -> None:
    """
    把使用者設定裡記的額外根目錄加回工作區
    Add the extra roots recorded in the user settings back to a workspace.

    設定檔可能被手動編輯，所以不是字串的項目會被略過。
    The settings file may have been edited by hand, so an entry that is not a
    string is skipped.

    :param workspace: 已經有主要根目錄的工作區 / a workspace that already has its primary root
    """
    stored = user_setting_dict.get(EXTRA_ROOTS_SETTING)
    for path in stored if isinstance(stored, list) else []:
        if isinstance(path, str) and path:
            workspace.add_root(ProjectRoot.from_path(path))


def remember_extra_roots(workspace: Workspace) -> None:
    """
    把主要根目錄以外的根目錄記進使用者設定
    Record the roots beyond the primary one in the user settings.

    主要根目錄就是工作目錄，設定檔本來就放在它底下，所以不必記。
    The primary root is the working directory, which the settings file already
    lives under, so it needs no recording.

    :param workspace: 要記錄的工作區 / the workspace to record
    """
    user_setting_dict[EXTRA_ROOTS_SETTING] = [
        root.path for root in workspace.roots[1:] if root.is_local]

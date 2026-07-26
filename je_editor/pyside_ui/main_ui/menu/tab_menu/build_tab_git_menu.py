from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.git_ui.code_diff_compare.code_diff_viewer_widget import DiffViewerWidget

from je_editor.utils.file_diff.unified import unified_diff_text

from je_editor.pyside_ui.git_ui.git_client.git_branch_tree_widget import GitTreeViewGUI

from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui

from je_editor.utils.logging.loggin_instance import jeditor_logger

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

def set_tab_git_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.tab_menu.git_menu = ui_we_want_to_set.tab_menu.addMenu(
        language_wrapper.language_word_dict.get("tab_menu_git_submenu_label")
    )
    # === Git Client 分頁 ===
    # === Git Client Tab ===
    ui_we_want_to_set.tab_menu.git_menu.add_git_client_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))
    ui_we_want_to_set.tab_menu.git_menu.add_git_client_ui_action.triggered.connect(
        lambda: add_git_client_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.git_menu.addAction(ui_we_want_to_set.tab_menu.git_menu.add_git_client_ui_action)

    # === Git Branch Tree 分頁 ===
    # === Git Branch Tree Tab ===
    ui_we_want_to_set.tab_menu.git_menu.add_git_branch_view_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_branch_tree_view_tab_name"))
    ui_we_want_to_set.tab_menu.git_menu.add_git_branch_view_ui_action.triggered.connect(
        lambda: add_git_tree_view_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.git_menu.addAction(ui_we_want_to_set.tab_menu.git_menu.add_git_branch_view_ui_action)

    # === Code Diff Viewer 分頁 ===
    # === Code Diff Viewer Tab ===
    ui_we_want_to_set.tab_menu.git_menu.add_code_diff_viewer_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_code_diff_viewer_tab_name"))
    ui_we_want_to_set.tab_menu.git_menu.add_code_diff_viewer_ui_action.triggered.connect(
        lambda: add_code_diff_compare_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.git_menu.addAction(ui_we_want_to_set.tab_menu.git_menu.add_code_diff_viewer_ui_action)

    # === 目前檔案與 HEAD 的差異 ===
    # === Diff the current file against HEAD ===
    ui_we_want_to_set.tab_menu.git_menu.add_file_diff_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_diff_against_head_name"))
    ui_we_want_to_set.tab_menu.git_menu.add_file_diff_action.triggered.connect(
        lambda: add_head_diff_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.git_menu.addAction(ui_we_want_to_set.tab_menu.git_menu.add_file_diff_action)

    # === 目前檔案與索引的差異 ===
    # === Diff the current file against what is staged ===
    ui_we_want_to_set.tab_menu.git_menu.add_staged_diff_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_diff_against_staged_name"))
    ui_we_want_to_set.tab_menu.git_menu.add_staged_diff_action.triggered.connect(
        lambda: add_staged_diff_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.git_menu.addAction(
        ui_we_want_to_set.tab_menu.git_menu.add_staged_diff_action)


def current_editor_widget(ui_we_want_to_set: EditorMain):
    """
    取得目前分頁的編輯器
    Return the editor in the current tab.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 編輯器分頁，目前分頁不是編輯器時為 ``None`` / the editor tab, or ``None``
    """
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return None
    widget = tab_widget.currentWidget()
    return widget if isinstance(widget, EditorWidget) else None


def head_diff_text(ui_we_want_to_set: EditorMain) -> str:
    """
    取得目前檔案相對於 HEAD 的差異
    Return the current file's diff against its committed version.

    使用編輯器已經在背景取得的基準，因此不需要再讀一次 git。
    Uses the baseline the editor already fetched in the background, so git is
    not read again.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: diff 文字；沒有可比較的內容時為空字串 / the diff, or an empty string
    """
    editor_widget = current_editor_widget(ui_we_want_to_set)
    if editor_widget is None:
        return ""
    code_edit = editor_widget.code_edit
    baseline = code_edit.diff_marker_manager.baseline()
    if baseline is None:
        return ""
    name = Path(code_edit.current_file).name if code_edit.current_file else ""
    return unified_diff_text(baseline, code_edit.toPlainText(), name)


def add_staged_diff_tab(ui_we_want_to_set: EditorMain) -> bool:
    """
    以並排比對開啟目前檔案與索引內容的差異
    Open the current file's diff against the index in the side-by-side viewer.

    逐段暫存之後，這是唯一能看出「已經放進索引的是哪些」的地方——與 HEAD 的差異
    看到的是全部改動，分不出哪些已經暫存。
    After staging hunk by hunk this is the only way to see what actually went into
    the index: the diff against HEAD shows every change, staged or not.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 有差異並開啟分頁時為 ``True`` / ``True`` when a tab was opened
    """
    jeditor_logger.info("build_tab_git_menu.py add staged diff tab")
    editor_widget = current_editor_widget(ui_we_want_to_set)
    if editor_widget is None:
        return False
    diff_text = editor_widget.code_edit.staged_diff_text()
    if not diff_text:
        return False
    viewer = DiffViewerWidget()
    viewer.viewer.set_diff_text(diff_text)
    ui_we_want_to_set.tab_widget.addTab(
        viewer,
        f"{language_wrapper.language_word_dict.get('tab_menu_diff_against_staged_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )
    return True


def add_head_diff_tab(ui_we_want_to_set: EditorMain) -> bool:
    """
    以並排比對開啟目前檔案與 HEAD 的差異
    Open the current file's diff against HEAD in the side-by-side viewer.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 有差異並開啟分頁時為 ``True`` / ``True`` when a tab was opened
    """
    jeditor_logger.info("build_tab_git_menu.py add head diff tab")
    diff_text = head_diff_text(ui_we_want_to_set)
    if not diff_text:
        return False
    viewer = DiffViewerWidget()
    viewer.viewer.set_diff_text(diff_text)
    ui_we_want_to_set.tab_widget.addTab(
        viewer,
        f"{language_wrapper.language_word_dict.get('tab_menu_diff_against_head_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )
    return True


def add_git_client_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 Git Client 分頁
    # Log: add a Git Client tab
    jeditor_logger.info(f"build_tab_menu.py add git client tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增 Git 客戶端分頁
    # Add a Git client tab
    ui_we_want_to_set.tab_widget.addTab(
        GitGui(),  # 建立 Git GUI 元件 / Create Git GUI widget
        f"{language_wrapper.language_word_dict.get('tab_menu_git_client_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_git_tree_view_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 Git Branch Tree 分頁
    # Log: add a Git Branch Tree tab
    jeditor_logger.info(f"build_tab_menu.py add git tree view tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增 Git 分支樹狀圖分頁
    # Add a Git branch tree view tab
    ui_we_want_to_set.tab_widget.addTab(
        GitTreeViewGUI(),  # 建立 Git Tree View 元件 / Create Git Tree View widget
        f"{language_wrapper.language_word_dict.get('tab_menu_git_branch_tree_view_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )

def add_code_diff_compare_tab(ui_we_want_to_set: EditorMain) -> None:
    # 紀錄日誌：新增 Code Diff Compare 分頁
    # Log: add a Code Diff Compare tab
    jeditor_logger.info(f"build_tab_menu.py add code diff compare tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增程式碼差異比較分頁
    # Add a code diff comparison tab
    ui_we_want_to_set.tab_widget.addTab(
        DiffViewerWidget(),  # 建立程式碼比對元件 / Create Code Diff Viewer widget
        f"{language_wrapper.language_word_dict.get('tab_code_diff_viewer_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )

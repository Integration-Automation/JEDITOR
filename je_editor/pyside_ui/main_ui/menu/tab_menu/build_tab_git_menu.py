from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.git_ui.code_diff_compare.code_diff_viewer_widget import DiffViewerWidget

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

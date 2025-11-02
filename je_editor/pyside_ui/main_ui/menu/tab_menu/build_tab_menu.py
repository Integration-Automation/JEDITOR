from __future__ import annotations

from typing import TYPE_CHECKING

from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget
from je_editor.pyside_ui.code.variable_inspector.inspector_gui import VariableInspector
# 匯入各種 UI 元件 (編輯器、瀏覽器、Git、變數檢查器、聊天、控制台、IPython、程式碼比對)
# Import various UI components (editor, browser, Git, variable inspector, chat, console, IPython, code diff)
from je_editor.pyside_ui.git_ui.code_diff_compare.code_diff_viewer_widget import DiffViewerWidget
from je_editor.pyside_ui.git_ui.git_client.git_branch_tree_widget import GitTreeViewGUI
from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI
from je_editor.pyside_ui.main_ui.console_widget.console_gui import ConsoleWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.ipython_widget.rich_jupyter import IpythonWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 啟用未來的註解功能，允許在型別提示中使用字串形式的前向參照
# Enable future annotations, allowing forward references in type hints
# TYPE_CHECKING 用於避免在型別檢查時引入不必要的模組
# TYPE_CHECKING is used to avoid unnecessary imports during type checking
# 匯入 FrontEngine 主 UI
# Import the FrontEngine main UI
# 匯入日誌工具，用於記錄操作
# Import logger for recording operations

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴
    # Import EditorMain only for type checking to avoid circular imports

from PySide6.QtGui import QAction
# 匯入 QAction，用於建立選單動作
# Import QAction for creating menu actions

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 匯入多語言包裝器，用於支援多語系 UI
# Import language wrapper for multilingual UI support


def set_tab_menu(ui_we_want_to_set: EditorMain) -> None:
    """
    設定主編輯器的分頁選單
    Set up the tab menu for the main editor
    """
    jeditor_logger.info(f"build_tab_menu.py set_tab_menu ui_we_want_to_set:{ui_we_want_to_set}")

    # 建立 Tab 選單 (主容器)
    # Create the Tab menu (main container)
    ui_we_want_to_set.tab_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("tab_menu_label")
    )

    # === Editor 分頁 ===
    # === Editor Tab ===
    ui_we_want_to_set.tab_menu.add_editor_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_editor_label"))
    ui_we_want_to_set.tab_menu.add_editor_action.triggered.connect(
        lambda: add_editor_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_editor_action)

    # === Front Engine 分頁 ===
    # === Front Engine Tab ===
    ui_we_want_to_set.tab_menu.add_frontengine_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_frontengine_label"))
    ui_we_want_to_set.tab_menu.add_frontengine_action.triggered.connect(
        lambda: add_frontengine_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_frontengine_action)

    # === Web 瀏覽器分頁 ===
    # === Web Browser Tab ===
    ui_we_want_to_set.tab_menu.add_web_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_web_label"))
    ui_we_want_to_set.tab_menu.add_web_action.triggered.connect(
        lambda: add_web_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_web_action)

    # === IPython 分頁 ===
    # === IPython Tab ===
    ui_we_want_to_set.tab_menu.add_ipython_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_ipython_tab_name"))
    ui_we_want_to_set.tab_menu.add_ipython_action.triggered.connect(
        lambda: add_ipython_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_ipython_action)

    # === Chat UI 分頁 ===
    # === Chat UI Tab ===
    ui_we_want_to_set.tab_menu.add_chat_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_chat_ui_tab_name"))
    ui_we_want_to_set.tab_menu.add_chat_ui_action.triggered.connect(
        lambda: add_chat_ui_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_chat_ui_action)

    # === Git Client 分頁 ===
    # === Git Client Tab ===
    ui_we_want_to_set.tab_menu.add_git_client_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))
    ui_we_want_to_set.tab_menu.add_git_client_ui_action.triggered.connect(
        lambda: add_git_client_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_git_client_ui_action)

    # === Git Branch Tree 分頁 ===
    # === Git Branch Tree Tab ===
    ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_branch_tree_view_tab_name"))
    ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action.triggered.connect(
        lambda: add_git_tree_view_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action)

    # === Variable Inspector 分頁 ===
    # === Variable Inspector Tab ===
    ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_variable_inspector_tab_name"))
    ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action.triggered.connect(
        lambda: add_variable_inspector_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action)

    # === Console 分頁 ===
    # === Console Tab ===
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_console_widget_tab_name"))
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action.triggered.connect(
        lambda: add_console_widget_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_console_widget_ui_action)

    # === Code Diff Viewer 分頁 ===
    # === Code Diff Viewer Tab ===
    ui_we_want_to_set.tab_menu.add_code_diff_viewer_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_code_diff_viewer_tab_name"))
    ui_we_want_to_set.tab_menu.add_code_diff_viewer_ui_action.triggered.connect(
        lambda: add_code_diff_compare_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_code_diff_viewer_ui_action)


# === 以下為各分頁新增函式 ===
# === Functions to add each tab ===

def add_editor_tab(ui_we_want_to_set: EditorMain):
    # 新增 Editor 分頁
    # Add Editor tab
    jeditor_logger.info(f"build_tab_menu.py add editor tab ui_we_want_to_set: {ui_we_want_to_set}")
    widget = EditorWidget(ui_we_want_to_set)
    ui_we_want_to_set.tab_widget.addTab(
        widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
    return widget


def add_frontengine_tab(ui_we_want_to_set: EditorMain):
    # 新增 FrontEngine 分頁
    # Add FrontEngine tab
    jeditor_logger.info(f"build_tab_menu.py add frontengine tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False),
        f"{language_wrapper.language_word_dict.get('tab_menu_frontengine_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_web_tab(ui_we_want_to_set: EditorMain):
    # 紀錄日誌：新增 Web 分頁
    # Log: add a Web tab
    jeditor_logger.info(f"build_tab_menu.py add web tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器的 tab_widget 中新增一個瀏覽器分頁
    # Add a browser tab into the main editor's tab_widget
    ui_we_want_to_set.tab_widget.addTab(
        MainBrowserWidget(),  # 建立瀏覽器元件 / Create browser widget
        f"{language_wrapper.language_word_dict.get('tab_menu_web_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"  # 分頁名稱包含序號 / Tab name with index
    )


def add_ipython_tab(ui_we_want_to_set: EditorMain):
    # 紀錄日誌：新增 IPython 分頁
    # Log: add an IPython tab
    jeditor_logger.info(f"build_tab_menu.py add ipython tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增 IPython 互動式分頁
    # Add an IPython interactive tab
    ui_we_want_to_set.tab_widget.addTab(
        IpythonWidget(ui_we_want_to_set),  # 建立 IPython 元件 / Create IPython widget
        f"{language_wrapper.language_word_dict.get('tab_menu_ipython_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_chat_ui_tab(ui_we_want_to_set: EditorMain):
    # 紀錄日誌：新增 Chat UI 分頁
    # Log: add a Chat UI tab
    jeditor_logger.info(f"build_tab_menu.py add chat_ui tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增聊天分頁
    # Add a chat tab into the main editor
    ui_we_want_to_set.tab_widget.addTab(
        ChatUI(ui_we_want_to_set),  # 建立聊天元件 / Create Chat UI widget
        f"{language_wrapper.language_word_dict.get('tab_menu_chat_ui_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_git_client_tab(ui_we_want_to_set: EditorMain):
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


def add_git_tree_view_tab(ui_we_want_to_set: EditorMain):
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


def add_variable_inspector_tab(ui_we_want_to_set: EditorMain):
    # 紀錄日誌：新增 Variable Inspector 分頁
    # Log: add a Variable Inspector tab
    jeditor_logger.info(f"build_tab_menu.py add variable inspector tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增變數檢查器分頁
    # Add a variable inspector tab
    ui_we_want_to_set.tab_widget.addTab(
        VariableInspector(),  # 建立變數檢查器元件 / Create Variable Inspector widget
        f"{language_wrapper.language_word_dict.get('tab_menu_variable_inspector_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_console_widget_tab(ui_we_want_to_set: EditorMain):
    # 紀錄日誌：新增 Console 分頁
    # Log: add a Console tab
    jeditor_logger.info(f"build_tab_menu.py add console widget tab ui_we_want_to_set: {ui_we_want_to_set}")
    # 在主編輯器中新增動態控制台分頁
    # Add a dynamic console tab
    ui_we_want_to_set.tab_widget.addTab(
        ConsoleWidget(),  # 建立控制台元件 / Create Console widget
        f"{language_wrapper.language_word_dict.get('tab_menu_console_widget_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}"
    )


def add_code_diff_compare_tab(ui_we_want_to_set: EditorMain):
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

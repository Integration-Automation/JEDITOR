from __future__ import annotations  # 啟用未來版本的型別註解功能 / Enable postponed evaluation of type annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog
from frontengine import FrontEngineMainUI  # 外部模組 FrontEngine 的主 UI / External FrontEngine main UI

from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget
from je_editor.pyside_ui.code.variable_inspector.inspector_gui import VariableInspector
# 匯入專案內的各種 Dockable widget / Import various dockable widgets from project
from je_editor.pyside_ui.git_ui.code_diff_compare.code_diff_viewer_widget import DiffViewerWidget
from je_editor.pyside_ui.git_ui.git_client.git_branch_tree_widget import GitTreeViewGUI
from je_editor.pyside_ui.git_ui.git_client.git_client_gui import GitGui
from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI
from je_editor.pyside_ui.main_ui.console_widget.console_gui import ConsoleWidget
from je_editor.pyside_ui.main_ui.dock.destroy_dock import DestroyDock
from je_editor.pyside_ui.main_ui.editor.editor_widget_dock import FullEditorWidget
from je_editor.pyside_ui.main_ui.ipython_widget.rich_jupyter import IpythonWidget
from je_editor.utils.file.open.open_file import read_file  # 檔案讀取工具 / File reading utility
from je_editor.utils.logging.loggin_instance import jeditor_logger  # 日誌紀錄器 / Logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper  # 多語系支援 / Multi-language wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain  # 僅在型別檢查時匯入 / Import only for type checking


def set_dock_menu(ui_we_want_to_set: EditorMain) -> None:
    """
    建立 Dock 功能選單，並加入各種 Dock 視窗的動作 (Action)。
    Create the Dock menu and add actions for different dockable widgets.
    """
    jeditor_logger.info(f"build_dock_menu.py set_dock_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # === 建立 Dock 主選單 / Create Dock main menu ===
    ui_we_want_to_set.dock_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("dock_menu_label"))

    # === 建立子選單 / Create Sub menu ===
    ui_we_want_to_set.dock_editor_menu = ui_we_want_to_set.dock_menu.addMenu(
        language_wrapper.language_word_dict.get("dock_editor_menu"))
    ui_we_want_to_set.dock_git_menu = ui_we_want_to_set.dock_menu.addMenu(
        language_wrapper.language_word_dict.get("dock_git_menu"))
    ui_we_want_to_set.dock_ai_menu = ui_we_want_to_set.dock_menu.addMenu(
        language_wrapper.language_word_dict.get("dock_ai_menu"))
    ui_we_want_to_set.dock_tools_menu = ui_we_want_to_set.dock_menu.addMenu(
        language_wrapper.language_word_dict.get("dock_tools_menu"))

    # === Browser Dock ===
    ui_we_want_to_set.dock_menu.new_dock_browser_action = QAction(
        language_wrapper.language_word_dict.get("dock_browser_label"))
    ui_we_want_to_set.dock_menu.new_dock_browser_action.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set)
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_dock_browser_action)

    # === Editor Dock ===
    ui_we_want_to_set.dock_menu.new_tab_dock_editor_action = QAction(
        language_wrapper.language_word_dict.get("dock_editor_label"))
    ui_we_want_to_set.dock_menu.new_tab_dock_editor_action.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "editor")
    )
    ui_we_want_to_set.dock_editor_menu.addAction(ui_we_want_to_set.dock_menu.new_tab_dock_editor_action)

    # === FrontEngine Dock ===
    ui_we_want_to_set.dock_menu.new_frontengine = QAction(
        language_wrapper.language_word_dict.get("dock_frontengine_label"))
    ui_we_want_to_set.dock_menu.new_frontengine.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "frontengine")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_frontengine)

    # === Ipython Dock ===
    ui_we_want_to_set.dock_menu.new_ipython = QAction(
        language_wrapper.language_word_dict.get("dock_ipython_label"))
    ui_we_want_to_set.dock_menu.new_ipython.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "ipython")
    )
    ui_we_want_to_set.dock_editor_menu.addAction(ui_we_want_to_set.dock_menu.new_ipython)

    # === ChatUI Dock ===
    ui_we_want_to_set.dock_menu.new_chat_ui = QAction(
        language_wrapper.language_word_dict.get("chat_ui_dock_label"))
    ui_we_want_to_set.dock_menu.new_chat_ui.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "chat_ui")
    )
    ui_we_want_to_set.dock_ai_menu.addAction(ui_we_want_to_set.dock_menu.new_chat_ui)

    # === Git Client Dock ===
    ui_we_want_to_set.dock_menu.new_git_client = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))
    ui_we_want_to_set.dock_menu.new_git_client.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "git_client")
    )
    ui_we_want_to_set.dock_git_menu.addAction(ui_we_want_to_set.dock_menu.new_git_client)

    # === Git Branch Tree View Dock ===
    ui_we_want_to_set.dock_menu.new_git_branch_view = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_branch_tree_view_tab_name"))
    ui_we_want_to_set.dock_menu.new_git_branch_view.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "git_branch_tree_view")
    )
    ui_we_want_to_set.dock_git_menu.addAction(ui_we_want_to_set.dock_menu.new_git_branch_view)

    # === Variable Inspector Dock ===
    ui_we_want_to_set.dock_menu.new_variable_inspector = QAction(
        language_wrapper.language_word_dict.get("tab_menu_variable_inspector_tab_name"))
    ui_we_want_to_set.dock_menu.new_variable_inspector.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "variable_inspector")
    )
    ui_we_want_to_set.dock_editor_menu.addAction(ui_we_want_to_set.dock_menu.new_variable_inspector)

    # === Console Dock ===
    ui_we_want_to_set.dock_menu.new_dynamic_console = QAction(
        language_wrapper.language_word_dict.get("tab_menu_console_widget_tab_name"))
    ui_we_want_to_set.dock_menu.new_dynamic_console.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "console_widget")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_dynamic_console)

    # === Code Diff Viewer Dock ===
    ui_we_want_to_set.dock_menu.new_code_diff_viewer = QAction(
        language_wrapper.language_word_dict.get("tab_code_diff_viewer_tab_name"))
    ui_we_want_to_set.dock_menu.new_code_diff_viewer.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "code_diff_viewer")
    )
    ui_we_want_to_set.dock_git_menu.addAction(ui_we_want_to_set.dock_menu.new_code_diff_viewer)


def add_dock_widget(ui_we_want_to_set: EditorMain, widget_type: str = None):
    """
    根據 widget_type 新增對應的 Dock 視窗，並加到主視窗右側。
    Add a dock widget based on widget_type and attach it to the right side of the main window.
    """
    jeditor_logger.info("build_dock_menu.py add_dock_widget "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"widget_type: {widget_type}")

    # 建立一個可銷毀的 Dock 容器
    # Create a destroyable dock container
    dock_widget = DestroyDock()

    if widget_type == "editor":
        # 開啟檔案選擇對話框，讓使用者選擇要打開的檔案
        # Open file dialog for selecting a file
        file_path = QFileDialog().getOpenFileName(
            parent=ui_we_want_to_set,
            dir=str(Path.cwd())  # 預設目錄為當前工作目錄 / Default directory is current working directory
        )[0]
        if file_path is not None and file_path != "":
            # 建立一個完整的編輯器 Dock，並載入檔案內容
            # Create a full editor dock and load file content
            widget = FullEditorWidget(current_file=file_path)
            file_content = read_file(file_path)[1]  # 讀取檔案內容 / Read file content
            widget.code_edit.setPlainText(file_content)
            dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_editor_title"))
            dock_widget.setWidget(widget)

    elif widget_type == "frontengine":
        # 建立 FrontEngine Dock
        # Create FrontEngine dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_frontengine_title"))
        dock_widget.setWidget(FrontEngineMainUI(redirect_output=False))

    elif widget_type == "ipython":
        # 建立 Ipython 互動式控制台 Dock
        # Create Ipython interactive console dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_ipython_title"))
        dock_widget.setWidget(IpythonWidget(ui_we_want_to_set))

    elif widget_type == "chat_ui":
        # 建立 ChatUI Dock
        # Create ChatUI dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("chat_ui_dock_label"))
        dock_widget.setWidget(ChatUI(ui_we_want_to_set))

    elif widget_type == "git_client":
        # 建立 Git 客戶端 Dock
        # Create Git client dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))
        dock_widget.setWidget(GitGui())

    elif widget_type == "git_branch_tree_view":
        # 建立 Git 分支樹視圖 Dock
        # Create Git branch tree view dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("tab_menu_git_branch_tree_view_tab_name"))
        dock_widget.setWidget(GitTreeViewGUI())

    elif widget_type == "variable_inspector":
        # 建立變數檢查器 Dock
        # Create variable inspector dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("tab_menu_variable_inspector_tab_name"))
        dock_widget.setWidget(VariableInspector())

    elif widget_type == "console_widget":
        # 建立動態 Console Dock
        # Create dynamic console dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("tab_menu_console_widget_tab_name"))
        dock_widget.setWidget(ConsoleWidget())

    elif widget_type == "code_diff_viewer":
        # 建立程式碼差異比較視圖 Dock
        # Create code diff viewer dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("tab_code_diff_viewer_tab_name"))
        dock_widget.setWidget(DiffViewerWidget())

    else:
        # 預設為瀏覽器 Dock
        # Default: Browser dock
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_browser_title"))
        dock_widget.setWidget(MainBrowserWidget())

    # 如果成功建立了 widget，將其加到主視窗右側 Dock 區域
    # If widget is created, add it to the right dock area of the main window
    if dock_widget.widget() is not None:
        ui_we_want_to_set.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

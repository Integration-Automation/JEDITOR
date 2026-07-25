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
from je_editor.pyside_ui.main_ui.ipython_widget.ipython_console import IpythonWidget
from je_editor.pyside_ui.main_ui.outline_panel.outline_panel_widget import OutlinePanelWidget
from je_editor.pyside_ui.main_ui.problems_panel.problems_panel_widget import ProblemsPanelWidget
from je_editor.pyside_ui.main_ui.test_panel.test_panel_widget import TestPanelWidget
from je_editor.pyside_ui.main_ui.todo_panel.todo_panel_widget import TodoPanelWidget
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

    # === TODO Panel Dock ===
    ui_we_want_to_set.dock_menu.new_todo_panel = QAction(
        language_wrapper.language_word_dict.get("tab_menu_todo_panel_tab_name"))
    ui_we_want_to_set.dock_menu.new_todo_panel.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "todo_panel")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_todo_panel)

    # === Problems Panel Dock ===
    ui_we_want_to_set.dock_menu.new_problems_panel = QAction(
        language_wrapper.language_word_dict.get("tab_menu_problems_panel_tab_name"))
    ui_we_want_to_set.dock_menu.new_problems_panel.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "problems_panel")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_problems_panel)

    # === Test Panel Dock ===
    ui_we_want_to_set.dock_menu.new_test_panel = QAction(
        language_wrapper.language_word_dict.get("tab_menu_test_panel_tab_name"))
    ui_we_want_to_set.dock_menu.new_test_panel.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "test_panel")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_test_panel)

    # === Outline Panel Dock ===
    ui_we_want_to_set.dock_menu.new_outline_panel = QAction(
        language_wrapper.language_word_dict.get("tab_menu_outline_panel_tab_name"))
    ui_we_want_to_set.dock_menu.new_outline_panel.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "outline_panel")
    )
    ui_we_want_to_set.dock_tools_menu.addAction(ui_we_want_to_set.dock_menu.new_outline_panel)


def _make_editor_dock(ui_we_want_to_set: EditorMain, dock_widget: "DestroyDock") -> bool:
    """建立 Editor Dock；取消選檔則回傳 False / Build editor dock, False if user cancels."""
    file_path = QFileDialog().getOpenFileName(
        parent=ui_we_want_to_set,
        dir=str(Path.cwd()),
    )[0]
    if not file_path:
        return False
    result = read_file(file_path)
    if result is None:
        return False
    widget = FullEditorWidget(current_file=file_path)
    widget.code_edit.setPlainText(result[1])
    dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_editor_title"))
    dock_widget.setWidget(widget)
    return True


def _dock_builders(ui_we_want_to_set: EditorMain) -> dict:
    """回傳 widget_type → (title_key, widget_factory) / Map dock type to title + widget factory."""
    return {
        "frontengine": ("dock_frontengine_title", lambda: FrontEngineMainUI(redirect_output=False)),
        "ipython": ("dock_ipython_title", lambda: IpythonWidget(ui_we_want_to_set)),
        "chat_ui": ("chat_ui_dock_label", lambda: ChatUI(ui_we_want_to_set)),
        "git_client": ("tab_menu_git_client_tab_name", GitGui),
        "git_branch_tree_view": ("tab_menu_git_branch_tree_view_tab_name", GitTreeViewGUI),
        "variable_inspector": ("tab_menu_variable_inspector_tab_name", VariableInspector),
        "console_widget": ("tab_menu_console_widget_tab_name", ConsoleWidget),
        "code_diff_viewer": ("tab_code_diff_viewer_tab_name", DiffViewerWidget),
        "todo_panel": ("tab_menu_todo_panel_tab_name",
                       lambda: TodoPanelWidget(ui_we_want_to_set)),
        "outline_panel": ("tab_menu_outline_panel_tab_name",
                          lambda: OutlinePanelWidget(ui_we_want_to_set)),
        "problems_panel": ("tab_menu_problems_panel_tab_name",
                           lambda: ProblemsPanelWidget(ui_we_want_to_set)),
        "test_panel": ("tab_menu_test_panel_tab_name",
                       lambda: TestPanelWidget(ui_we_want_to_set)),
    }


def add_dock_widget(ui_we_want_to_set: EditorMain, widget_type: str = None) -> None:
    """根據 widget_type 新增對應的 Dock 視窗 / Add a dock widget based on widget_type."""
    jeditor_logger.info("build_dock_menu.py add_dock_widget "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"widget_type: {widget_type}")

    dock_widget = DestroyDock()

    if widget_type == "editor":
        if not _make_editor_dock(ui_we_want_to_set, dock_widget):
            return
    else:
        builder = _dock_builders(ui_we_want_to_set).get(widget_type)
        if builder is not None:
            title_key, factory = builder
            dock_widget.setWindowTitle(language_wrapper.language_word_dict.get(title_key))
            dock_widget.setWidget(factory())
        else:
            dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_browser_title"))
            dock_widget.setWidget(MainBrowserWidget())

    if dock_widget.widget() is not None:
        ui_we_want_to_set.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

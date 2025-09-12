from __future__ import annotations

from typing import TYPE_CHECKING

from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
from je_editor.pyside_ui.code.variable_inspector.inspector_gui import VariableInspector
from je_editor.pyside_ui.git.git_branch_tree_widget import GitTreeViewGUI
from je_editor.pyside_ui.git.git_client_gui import Gitgui
from je_editor.pyside_ui.main_ui.ai_widget.chat_ui import ChatUI
from je_editor.pyside_ui.main_ui.console_widget.console_gui import ConsoleWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.ipython_widget.rich_jupyter import IpythonWidget
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_tab_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_tab_menu.py set_tab_menu ui_we_want_to_set:{ui_we_want_to_set}")
    # Editor
    ui_we_want_to_set.tab_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("tab_menu_label")
    )
    ui_we_want_to_set.tab_menu.add_editor_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_editor_label"))
    ui_we_want_to_set.tab_menu.add_editor_action.triggered.connect(
        lambda: add_editor_tab(ui_we_want_to_set)
    )
    # Front Engine
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_editor_action)
    ui_we_want_to_set.tab_menu.add_frontengine_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_frontengine_label"))
    ui_we_want_to_set.tab_menu.add_frontengine_action.triggered.connect(
        lambda: add_frontengine_tab(ui_we_want_to_set)
    )
    # Web
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_frontengine_action)
    ui_we_want_to_set.tab_menu.add_web_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_web_label"))
    ui_we_want_to_set.tab_menu.add_web_action.triggered.connect(
        lambda: add_web_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_web_action)
    # Stackoverflow
    ui_we_want_to_set.tab_menu.add_stackoverflow_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_stackoverflow_label"))
    ui_we_want_to_set.tab_menu.add_stackoverflow_action.triggered.connect(
        lambda: add_stackoverflow_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_stackoverflow_action)
    # IPython
    ui_we_want_to_set.tab_menu.add_ipython_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_ipython_tab_name"))
    ui_we_want_to_set.tab_menu.add_ipython_action.triggered.connect(
        lambda: add_ipython_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_ipython_action)
    # ChatUI
    ui_we_want_to_set.tab_menu.add_chat_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_chat_ui_tab_name"))
    ui_we_want_to_set.tab_menu.add_chat_ui_action.triggered.connect(
        lambda: add_chat_ui_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_chat_ui_action)
    # Git Client
    ui_we_want_to_set.tab_menu.add_git_client_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_client_tab_name"))
    ui_we_want_to_set.tab_menu.add_git_client_ui_action.triggered.connect(
        lambda: add_git_client_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_git_client_ui_action)
    # Git Branch tree
    ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_git_branch_tree_view_tab_name"))
    ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action.triggered.connect(
        lambda: add_git_tree_view_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_git_branch_view_ui_action)
    # Variable Inspector
    ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_variable_inspector_tab_name"))
    ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action.triggered.connect(
        lambda: add_variable_inspector_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_variable_inspector_ui_action)
    # Dynamic Console
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_console_widget_tab_name"))
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action.triggered.connect(
        lambda: add_console_widget_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_console_widget_ui_action)

def add_editor_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add editor tab ui_we_want_to_set: {ui_we_want_to_set}")
    widget = EditorWidget(ui_we_want_to_set)
    ui_we_want_to_set.tab_widget.addTab(
        widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
    return widget


def add_frontengine_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add frontengine tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False),
        f"{language_wrapper.language_word_dict.get('tab_menu_frontengine_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_web_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add web tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        BrowserWidget(),
        f"{language_wrapper.language_word_dict.get('tab_menu_web_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_stackoverflow_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add stackoverflow tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        BrowserWidget(start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="),
        f"{language_wrapper.language_word_dict.get('tab_menu_stackoverflow_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_ipython_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add ipython tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        IpythonWidget(ui_we_want_to_set),
        f"{language_wrapper.language_word_dict.get('tab_menu_ipython_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_chat_ui_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add chat_ui tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        ChatUI(ui_we_want_to_set),
        f"{language_wrapper.language_word_dict.get('tab_menu_chat_ui_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_git_client_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add git client tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        Gitgui(),
        f"{language_wrapper.language_word_dict.get('tab_menu_git_client_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")

def add_git_tree_view_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add git tree view tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        GitTreeViewGUI(),
        f"{language_wrapper.language_word_dict.get('tab_menu_git_branch_tree_view_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")

def add_variable_inspector_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add variable inspector tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        VariableInspector(),
        f"{language_wrapper.language_word_dict.get('tab_menu_variable_inspector_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_console_widget_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add console widget tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        ConsoleWidget(),
        f"{language_wrapper.language_word_dict.get('tab_menu_console_widget_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
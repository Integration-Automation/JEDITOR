from __future__ import annotations

from typing import TYPE_CHECKING

from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.browser_widget import JEBrowser
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.ipython_widget.rich_jupyter import IpythonWidget
from re_edge_gpt.ui.chat.main_ui import ChatMainUI

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_tab_menu(ui_we_want_to_set: EditorMain) -> None:
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
        lambda: add_stackoverflow(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_stackoverflow_action)
    # IPython
    ui_we_want_to_set.tab_menu.add_ipython_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_ipython_tab_name"))
    ui_we_want_to_set.tab_menu.add_ipython_action.triggered.connect(
        lambda: add_ipython(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_ipython_action)
    # ReEdgeGPT
    ui_we_want_to_set.tab_menu.add_re_edge_gpt_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_re_re_edge_gpt_tab_name"))
    ui_we_want_to_set.tab_menu.add_re_edge_gpt_action.triggered.connect(
        lambda: add_re_edge_gpt(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_re_edge_gpt_action)


def add_editor_tab(ui_we_want_to_set: EditorMain):
    widget = EditorWidget(ui_we_want_to_set)
    ui_we_want_to_set.tab_widget.addTab(
        widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
    return widget


def add_frontengine_tab(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False),
        f"{language_wrapper.language_word_dict.get('tab_menu_frontengine_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_web_tab(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        JEBrowser(),
        f"{language_wrapper.language_word_dict.get('tab_menu_web_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_stackoverflow(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        JEBrowser(start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="),
        f"{language_wrapper.language_word_dict.get('tab_menu_stackoverflow_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_ipython(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        IpythonWidget(ui_we_want_to_set),
        f"{language_wrapper.language_word_dict.get('tab_menu_ipython_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_re_edge_gpt(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        ChatMainUI(),
        f"{language_wrapper.language_word_dict.get('tab_name_re_edge_gpt')} "
        f"{ui_we_want_to_set.tab_widget.count()}")

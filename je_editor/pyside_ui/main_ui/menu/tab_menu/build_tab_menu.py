from __future__ import annotations

from typing import TYPE_CHECKING

from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.browser_widget import BrowserWidget
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


def add_editor_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add_editor_tab ui_we_want_to_set: {ui_we_want_to_set}")
    widget = EditorWidget(ui_we_want_to_set)
    ui_we_want_to_set.tab_widget.addTab(
        widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
    return widget


def add_frontengine_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add_frontengine_tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False, redirect_output=False),
        f"{language_wrapper.language_word_dict.get('tab_menu_frontengine_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_web_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add_web_tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        BrowserWidget(),
        f"{language_wrapper.language_word_dict.get('tab_menu_web_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_stackoverflow_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add_stackoverflow_tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        BrowserWidget(start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="),
        f"{language_wrapper.language_word_dict.get('tab_menu_stackoverflow_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


def add_ipython_tab(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_tab_menu.py add_ipython_tab ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.tab_widget.addTab(
        IpythonWidget(ui_we_want_to_set),
        f"{language_wrapper.language_word_dict.get('tab_menu_ipython_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")


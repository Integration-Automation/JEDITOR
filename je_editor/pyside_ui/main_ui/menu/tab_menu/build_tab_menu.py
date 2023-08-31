from __future__ import annotations

from typing import TYPE_CHECKING

from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.je_broser import JEBrowser
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtGui import QAction


def set_tab_menu(ui_we_want_to_set: EditorMain) -> None:
    ui_we_want_to_set.tab_menu = ui_we_want_to_set.menu.addMenu("Tab")
    ui_we_want_to_set.tab_menu.add_editor_action = QAction("Add Editor Tab")
    ui_we_want_to_set.tab_menu.add_editor_action.triggered.connect(
        lambda: add_editor_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_editor_action)
    ui_we_want_to_set.tab_menu.add_frontengine_action = QAction("Add FrontEngine Tab")
    ui_we_want_to_set.tab_menu.add_frontengine_action.triggered.connect(
        lambda: add_frontengine_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_frontengine_action)
    ui_we_want_to_set.tab_menu.add_web_action = QAction("Add WEB Tab")
    ui_we_want_to_set.tab_menu.add_web_action.triggered.connect(
        lambda: add_web_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_web_action)


def add_editor_tab(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        EditorWidget(), f"Editor {ui_we_want_to_set.tab_widget.count()}")


def add_frontengine_tab(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        FrontEngineMainUI(show_system_tray_ray=False), f"FrontEngine {ui_we_want_to_set.tab_widget.count()}")


def add_web_tab(ui_we_want_to_set: EditorMain):
    ui_we_want_to_set.tab_widget.addTab(
        JEBrowser(), f"Web Browser {ui_we_want_to_set.tab_widget.count()}")

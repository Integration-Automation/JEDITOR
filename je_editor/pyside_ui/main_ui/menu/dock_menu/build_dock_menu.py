from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog
from frontengine import FrontEngineMainUI

from je_editor.pyside_ui.browser.browser_widget import JEBrowser
from je_editor.pyside_ui.main_ui.dock.destroy_dock import DestroyDock
from je_editor.pyside_ui.main_ui.editor.editor_widget_dock import FullEditorWidget
from je_editor.pyside_ui.main_ui.ipython_widget.rich_jupyter import IpythonWidget
from je_editor.utils.file.open.open_file import read_file
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_dock_menu(ui_we_want_to_set: EditorMain) -> None:
    # Browser
    ui_we_want_to_set.dock_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("dock_menu_label"))
    ui_we_want_to_set.dock_menu.new_dock_browser_action = QAction(
        language_wrapper.language_word_dict.get("dock_browser_label"))
    ui_we_want_to_set.dock_menu.new_dock_browser_action.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set)
    )
    ui_we_want_to_set.dock_menu.addAction(ui_we_want_to_set.dock_menu.new_dock_browser_action)
    # Stackoverflow
    ui_we_want_to_set.dock_menu.new_dock_stackoverflow_action = QAction(
        language_wrapper.language_word_dict.get("dock_stackoverflow_label"))
    ui_we_want_to_set.dock_menu.new_dock_stackoverflow_action.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "stackoverflow")
    )
    ui_we_want_to_set.dock_menu.addAction(ui_we_want_to_set.dock_menu.new_dock_stackoverflow_action)
    # Editor
    ui_we_want_to_set.dock_menu.new_tab_dock_editor_action = QAction(
        language_wrapper.language_word_dict.get("dock_editor_label"))
    ui_we_want_to_set.dock_menu.new_tab_dock_editor_action.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "editor")
    )
    ui_we_want_to_set.dock_menu.addAction(ui_we_want_to_set.dock_menu.new_tab_dock_editor_action)
    # FrontEngine
    ui_we_want_to_set.dock_menu.new_frontengine = QAction(
        language_wrapper.language_word_dict.get("dock_frontengine_label"))
    ui_we_want_to_set.dock_menu.new_frontengine.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "frontengine")
    )
    ui_we_want_to_set.dock_menu.addAction(ui_we_want_to_set.dock_menu.new_frontengine)
    # Ipython
    ui_we_want_to_set.dock_menu.new_ipython = QAction(
        language_wrapper.language_word_dict.get("dock_ipython_label"))
    ui_we_want_to_set.dock_menu.new_ipython.triggered.connect(
        lambda: add_dock_widget(ui_we_want_to_set, "ipython")
    )
    ui_we_want_to_set.dock_menu.addAction(ui_we_want_to_set.dock_menu.new_ipython)


def add_dock_widget(ui_we_want_to_set: EditorMain, widget_type: str = None):
    # Dock widget
    dock_widget = DestroyDock()
    if widget_type == "stackoverflow":
        dock_widget.setWindowTitle("stackoverflow")
        dock_widget.setWidget(JEBrowser(
            start_url="https://stackoverflow.com/", search_prefix="https://stackoverflow.com/search?q="))
    elif widget_type == "editor":
        file_path = QFileDialog().getOpenFileName(
            parent=ui_we_want_to_set,
            dir=str(Path.cwd())
        )[0]
        if file_path is not None and file_path != "":
            widget = FullEditorWidget(current_file=file_path)
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(
                file_content
            )
            dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_editor_title"))
            dock_widget.setWidget(widget)
    elif widget_type == "frontengine":
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_frontengine_title"))
        dock_widget.setWidget(FrontEngineMainUI())
    elif widget_type == "ipython":
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_ipython_title"))
        dock_widget.setWidget(IpythonWidget(ui_we_want_to_set))
    else:
        dock_widget.setWindowTitle(language_wrapper.language_word_dict.get("dock_browser_title"))
        dock_widget.setWidget(JEBrowser())
    if dock_widget.widget() is not None:
        ui_we_want_to_set.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_widget)

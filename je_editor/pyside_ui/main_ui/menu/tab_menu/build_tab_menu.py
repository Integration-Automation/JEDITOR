from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu

from je_editor.pyside_ui.browser.main_browser_widget import MainBrowserWidget
from je_editor.pyside_ui.main_ui.console_widget.console_gui import ConsoleWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_git_menu import set_tab_git_menu
from je_editor.pyside_ui.main_ui.menu.tab_menu.build_tab_tools_menu import set_tab_tools_menu
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtGui import QAction

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


def set_tab_menu(ui_we_want_to_set: EditorMain) -> None:
    """
    設定主編輯器的分頁選單
    Set up the tab menu for the main editor
    """
    jeditor_logger.info(f"build_tab_menu.py set_tab_menu ui_we_want_to_set:{ui_we_want_to_set}")

    # 建立 Tab 選單 (主容器)
    # Create the Tab menu (main container)
    ui_we_want_to_set.tab_menu: QMenu = ui_we_want_to_set.menu.addMenu(
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

    # === Web 瀏覽器分頁 ===
    # === Web Browser Tab ===
    ui_we_want_to_set.tab_menu.add_web_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_add_web_label"))
    ui_we_want_to_set.tab_menu.add_web_action.triggered.connect(
        lambda: add_web_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_web_action)

    # === Console 分頁 ===
    # === Console Tab ===
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_console_widget_tab_name"))
    ui_we_want_to_set.tab_menu.add_console_widget_ui_action.triggered.connect(
        lambda: add_console_widget_tab(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.add_console_widget_ui_action)

    # === 同檔分割檢視 ===
    # === Split view of the same file ===
    ui_we_want_to_set.tab_menu.toggle_split_view_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_split_view_label"))
    ui_we_want_to_set.tab_menu.toggle_split_view_action.setShortcut("Ctrl+Alt+\\")
    ui_we_want_to_set.tab_menu.toggle_split_view_action.triggered.connect(
        lambda: toggle_split_view(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.toggle_split_view_action)

    # === 縮圖 ===
    # === Minimap ===
    ui_we_want_to_set.tab_menu.toggle_minimap_action = QAction(
        language_wrapper.language_word_dict.get("tab_menu_minimap_label"))
    ui_we_want_to_set.tab_menu.toggle_minimap_action.setShortcut("Ctrl+Alt+M")
    ui_we_want_to_set.tab_menu.toggle_minimap_action.triggered.connect(
        lambda: toggle_minimap(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.toggle_minimap_action)

    # === 片段編輯器 ===
    # === Snippet editor ===
    ui_we_want_to_set.tab_menu.edit_snippets_action = QAction(
        language_wrapper.language_word_dict.get("snippet_editor_title"))
    ui_we_want_to_set.tab_menu.edit_snippets_action.triggered.connect(
        lambda: show_snippet_editor(ui_we_want_to_set)
    )
    ui_we_want_to_set.tab_menu.addAction(ui_we_want_to_set.tab_menu.edit_snippets_action)

    set_tab_tools_menu(ui_we_want_to_set=ui_we_want_to_set)
    set_tab_git_menu(ui_we_want_to_set=ui_we_want_to_set)


def show_snippet_editor(ui_we_want_to_set: EditorMain):
    """
    開啟片段編輯器
    Open the snippet editor.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 開啟的對話框 / the dialog that was opened
    """
    jeditor_logger.info("build_tab_menu.py show_snippet_editor")
    from je_editor.pyside_ui.dialog.snippet_dialog.snippet_editor_dialog import (
        SnippetEditorDialog
    )
    dialog = SnippetEditorDialog(ui_we_want_to_set)
    dialog.show()
    return dialog


def toggle_minimap(ui_we_want_to_set: EditorMain) -> bool:
    """
    切換目前分頁的縮圖
    Toggle the current tab's minimap.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 切換後是否為開啟 / whether the minimap is now shown
    """
    jeditor_logger.info("build_tab_menu.py toggle_minimap")
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return False
    widget = tab_widget.currentWidget()
    if not isinstance(widget, EditorWidget):
        return False
    return widget.toggle_minimap()


def toggle_split_view(ui_we_want_to_set: EditorMain) -> bool:
    """
    切換目前分頁的同檔分割檢視
    Toggle the split view of the current tab's file.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :return: 切換後是否為開啟 / whether the split view is now shown
    """
    jeditor_logger.info("build_tab_menu.py toggle_split_view")
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return False
    widget = tab_widget.currentWidget()
    if not isinstance(widget, EditorWidget):
        return False
    return widget.toggle_split_view()


# === 以下為各分頁新增函式 ===
# === Functions to add each tab ===

def add_editor_tab(ui_we_want_to_set: EditorMain) -> EditorWidget:
    # 新增 Editor 分頁
    # Add Editor tab
    jeditor_logger.info(f"build_tab_menu.py add editor tab ui_we_want_to_set: {ui_we_want_to_set}")
    widget = EditorWidget(ui_we_want_to_set)
    ui_we_want_to_set.tab_widget.addTab(
        widget,
        f"{language_wrapper.language_word_dict.get('tab_menu_editor_tab_name')} "
        f"{ui_we_want_to_set.tab_widget.count()}")
    return widget


def add_web_tab(ui_we_want_to_set: EditorMain) -> None:
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


def add_console_widget_tab(ui_we_want_to_set: EditorMain) -> None:
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

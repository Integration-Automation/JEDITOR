"""
換語言後把整個介面重新標示一次
Relabel the whole interface after the language changes.

原本換語言只會跳出「請重新啟動」——設定改了，但畫面上一個字也沒變。選單與工具列
是啟動時建好的，重建它們最省事也最完整；面板各自有狀態，因此由它們自己重新標示。
Changing the language used to do nothing but ask for a restart: the setting
moved and not one word on screen did. The menus and the toolbar are built at
startup and rebuilding them is both the simplest and the most complete way to
relabel them; the panels hold state, so each relabels itself.
"""
from __future__ import annotations

from typing import Dict

from je_editor.pyside_ui.main_ui.save_settings.shortcut_setting import reload_bound_shortcuts
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.multi_language.retranslate_text import TITLE_KEYS, translated_again


def retranslate_ui(main_window, previous_words: Dict[str, str]) -> None:
    """
    依目前語言重新標示整個介面
    Relabel the whole interface in the language now in use.

    :param main_window: 主編輯器視窗 / the main editor window
    :param previous_words: 換語言之前的字典 / the dictionary from before the change
    """
    jeditor_logger.info("retranslate.py retranslate_ui")
    words = language_wrapper.language_word_dict
    main_window.setWindowTitle(words.get("application_name", ""))
    main_window.setToolTip(words.get("application_name", ""))
    _rebuild_menu_bar(main_window)
    _rebuild_toolbar(main_window)
    _retranslate_tabs(main_window, previous_words, words)
    _retranslate_docks(main_window, previous_words, words)
    refresh = getattr(main_window, "refresh_status_bar", None)
    if callable(refresh):
        refresh()
    # 舊選單與工具列的動作已經消失，把它們從快捷鍵表中清掉
    # The old menu and toolbar actions are gone; drop them from the shortcut table
    reload_bound_shortcuts()


def _rebuild_menu_bar(main_window) -> None:
    """重建選單列 / Build the menu bar again."""
    from je_editor.pyside_ui.main_ui.menu.set_menu_bar import set_menu_bar
    # setMenuBar 會接手並刪掉舊的那一個 / setMenuBar takes over and deletes the old one
    set_menu_bar(main_window)


def _rebuild_toolbar(main_window) -> None:
    """
    重建工具列
    Build the toolbar again.

    先等舊工具列的背景工作結束：git 分支掃描完成後要去填那個下拉選單，而下拉選單
    正要被刪掉。不等的話 Qt 會直接讓程序中止。
    The outgoing toolbar's background work is waited for first: the git branch
    scan finishes by filling that combo box, and the combo box is about to be
    deleted. Without the wait, Qt aborts the process.
    """
    from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
        build_toolbar, stop_background_threads
    )
    stop_background_threads()
    old = getattr(main_window, "main_toolbar", None)
    if old is not None:
        main_window.removeToolBar(old)
        old.deleteLater()
    build_toolbar(main_window)


def _retranslate_tabs(main_window, previous: Dict[str, str], current: Dict[str, str]) -> None:
    """
    重新標示分頁標題，檔名保持原樣
    Relabel the tab titles, leaving file names alone.
    """
    tab_widget = getattr(main_window, "tab_widget", None)
    if tab_widget is None:
        return
    for index in range(tab_widget.count()):
        tab_widget.setTabText(
            index, translated_again(tab_widget.tabText(index), previous, current, TITLE_KEYS))
        _retranslate_widget(tab_widget.widget(index))


def _retranslate_docks(main_window, previous: Dict[str, str], current: Dict[str, str]) -> None:
    """重新標示浮動視窗的標題與內容 / Relabel the docks and what they hold."""
    from PySide6.QtWidgets import QDockWidget
    for dock in main_window.findChildren(QDockWidget):
        dock.setWindowTitle(
            translated_again(dock.windowTitle(), previous, current, TITLE_KEYS))
        _retranslate_widget(dock.widget())


def _retranslate_widget(widget) -> None:
    """
    請一個元件重新標示自己
    Ask a widget to relabel itself.

    有 ``retranslate`` 就呼叫它。沒有的元件維持原本的字，直到重新開啟為止——這比
    硬把它拆掉重建安全，因為那會連同它記著的狀態一起丟掉。
    A widget with a ``retranslate`` is asked to. One without keeps its wording
    until it is reopened, which is safer than tearing it down and rebuilding it:
    that would throw away whatever state it is holding.
    """
    retranslate = getattr(widget, "retranslate", None)
    if callable(retranslate):
        retranslate()

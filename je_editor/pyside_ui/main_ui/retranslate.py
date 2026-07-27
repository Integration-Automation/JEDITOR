"""
換語言後把整個介面重新標示一次
Relabel the whole interface after the language changes.

原本換語言只會跳出「請重新啟動」——設定改了，但畫面上一個字也沒變。
Changing the language used to do nothing but ask for a restart: the setting
moved and not one word on screen did.

這裡只改字，不動任何 widget。曾經是整條選單列重建（``setMenuBar`` 會把舊的連同
底下所有選單一起刪掉），對 JEditor 自己沒差，但把自己的選單掛在同一條列上的宿主
程式會整組消失，而它留著的參考就成了指向已刪物件的指標——碰到就是當掉。
Nothing here is torn down; only the wording moves. The menu bar used to be
rebuilt, and ``setMenuBar`` deletes the outgoing bar together with every menu on
it. That costs JEditor nothing, since it owns them all, but an application
embedding this window adds its menus to that same bar: they vanish, and the
references it still holds become pointers to deleted objects, which crash as
soon as anything follows one.
"""
from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtWidgets import QComboBox, QLabel, QMenuBar, QToolBar, QWidgetAction

from je_editor.pyside_ui.main_ui.menu.submenu_map import submenus_of
from je_editor.pyside_ui.main_ui.save_settings.shortcut_setting import reload_bound_shortcuts
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper
from je_editor.utils.multi_language.retranslate_text import (
    TITLE_KEYS, family_of, key_for_text, keys_in_family, menu_candidates,
    translated_again
)

# 工具列的鍵都在這個家族底下 / The toolbar's keys all live in this family
TOOLBAR_FAMILY = "toolbar"


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
    _retranslate_menu_bar(main_window, previous_words, words)
    _retranslate_toolbar(main_window, previous_words, words)
    _retranslate_tabs(main_window, previous_words, words)
    _retranslate_docks(main_window, previous_words, words)
    refresh = getattr(main_window, "refresh_status_bar", None)
    if callable(refresh):
        refresh()
    # 使用者改過的快捷鍵重新套用一次 / Re-apply the keys the user reassigned
    reload_bound_shortcuts()


def _retranslate_menu_bar(main_window, previous: Dict[str, str],
                          current: Dict[str, str]) -> None:
    """
    重新標示選單列上的每一個選單與項目
    Relabel every menu and item on the menu bar.

    宿主程式加的選單一併換掉——它的字也在同一份字典裡——而檔名、直譯器路徑這類認
    不出來的文字保持原樣。
    Menus an embedding application added move too, since their wording is in the
    same dictionary, while text that cannot be placed -- a file name, an
    interpreter's path -- is left exactly as it is.
    """
    menu_bar = getattr(main_window, "menu", None)
    if not isinstance(menu_bar, QMenuBar):
        menu_bar = main_window.menuBar()
    if menu_bar is None:
        return
    listings = _menus_that_list_names(main_window)
    submenu_of = submenus_of(menu_bar)

    def walk(action, family: str, top_level: bool = False) -> None:
        key = _relabel_in_stages(action, previous, current, family, top_level)
        submenu = submenu_of.get(action)
        if submenu is None or submenu in listings:
            return
        inner = family_of(key) or family
        for child in submenu.actions():
            walk(child, inner)

    for entry in menu_bar.actions():
        walk(entry, family="", top_level=True)


def _menus_that_list_names(main_window) -> set:
    """
    列的是名字而不是說法的選單，裡面的項目不要動
    The menus listing names rather than wording, whose items are left alone.

    語言選單的每一項都是某個語言自己的寫法（English、繁體中文、日本語）——看不懂
    目前介面語言的人，就是靠這個找到自己的那一個。字型選單列的是系統裝了哪些字
    型，其中 ``Symbol`` 與 ``Terminal`` 剛好也是字典裡別處的英文字，照翻就會把字
    型名稱換成不存在的字型。
    Every entry in the Language menu is a language's own name for itself, which
    is how someone who cannot read the current interface language finds theirs.
    The font menus list what is installed, and two of those families -- ``Symbol``
    and ``Terminal`` -- happen to read like words used elsewhere in the
    dictionary, so translating them would name fonts that do not exist.

    最近開啟的檔案不必列在這裡：那些項目是完整路徑，本來就對不上字典裡任何一個
    字，而檔案清單空的時候顯示的那句話則應該跟著語言走。
    Recent files need no entry here: those items are full paths and so match
    nothing in the dictionary, while the line shown when the list is empty is
    wording and should move with the language.

    :param main_window: 主編輯器視窗 / the main editor window
    :return: 這些選單 / those menus
    """
    menus = {getattr(main_window, "language_menu", None)}
    for owner_name in ("file_menu", "text_menu"):
        owner = getattr(main_window, owner_name, None)
        menus.add(getattr(owner, "font_menu", None))
    return {menu for menu in menus if menu is not None}


def _relabel_in_stages(action, previous: Dict[str, str], current: Dict[str, str],
                       family: str, top_level: bool = False) -> Optional[str]:
    """
    依序用越來越寬的候選鍵去認一個項目的文字
    Place one item's text against widening sets of candidate keys.

    選單列上那一排的鍵都叫 ``..._menu_label``，先只看這一批：宿主程式併進來的字典
    可能也有一個字寫著 ``Run``，而那個鍵不見得每個語言都翻了。
    A menu bar entry's key is always named ``..._menu_label``, so those come
    first: a dictionary merged in by an embedding application may well have its
    own key reading ``Run``, and that one need not be translated everywhere.

    接著找同一個家族的鍵：子選單的項目與它所屬的選單同一個家族，這樣「分頁選單裡
    的 Editor」不會被「浮動視窗選單裡的 Editor」蓋掉。再放寬到所有選單的鍵，最後
    才是整本字典——有些項目的鍵既不帶 ``_menu`` 也不以 ``_label`` 結尾。
    Then comes the family, since a submenu's items share the family of the menu
    holding them, which keeps the Tab menu's "Editor" from being given the Dock
    menu's wording. Then every menu key, and last the whole dictionary: some
    items' keys carry neither ``_menu`` nor ``_label``.

    :return: 對應的鍵，認不出來時為 ``None`` / the key, or ``None``
    """
    for candidates in (
        _menu_bar_keys(previous) if top_level else (),
        keys_in_family(previous, family) if family else (),
        menu_candidates(previous),
        tuple(previous),
    ):
        if not candidates:
            continue
        key = _relabel(action, previous, current, candidates)
        if key is not None:
            return key
    return None


def _menu_bar_keys(words: Dict[str, str]) -> tuple:
    """選單列上那一排的鍵 / The keys naming the menu bar's own entries."""
    return tuple(key for key in words if key.endswith("_menu_label"))


def _relabel(action, previous: Dict[str, str], current: Dict[str, str],
             candidates) -> Optional[str]:
    """
    把一個項目的文字與提示換成新語言的說法
    Move one item's text, and its tip, to the new language's wording.

    :return: 這段文字對應的鍵，認不出來時為 ``None`` / the key behind the text,
        or ``None`` when it cannot be placed
    """
    key = key_for_text(action.text(), previous, candidates)
    if key is None:
        return None
    tip_follows_text = action.toolTip() == action.text()
    action.setText(current.get(key, action.text()))
    if tip_follows_text:
        action.setToolTip(action.text())
    else:
        action.setToolTip(
            translated_again(action.toolTip(), previous, current, candidates))
    return key


def _retranslate_toolbar(main_window, previous: Dict[str, str],
                         current: Dict[str, str]) -> None:
    """
    重新標示工具列
    Relabel the toolbar.

    下拉選單裡的分支名稱不是翻譯來的，因此只換它的提示。
    The branch names in the combo box did not come from a translation, so only
    its tip moves.
    """
    from je_editor.pyside_ui.main_ui.toolbar.toolbar_builder import (
        GIT_BRANCH_LABEL_NAME, git_branch_label_text
    )
    toolbar = getattr(main_window, "main_toolbar", None)
    if not isinstance(toolbar, QToolBar):
        return
    toolbar_keys = tuple(
        key for key in previous if key.startswith(f"{TOOLBAR_FAMILY}_"))
    toolbar.setWindowTitle(
        translated_again(toolbar.windowTitle(), previous, current, toolbar_keys))
    for action in toolbar.actions():
        if isinstance(action, QWidgetAction):
            _retranslate_toolbar_widget(
                action.defaultWidget(), previous, current, toolbar_keys,
                GIT_BRANCH_LABEL_NAME, git_branch_label_text)
            continue
        _relabel(action, previous, current, toolbar_keys)


def _retranslate_toolbar_widget(widget, previous: Dict[str, str],
                                current: Dict[str, str], candidates,
                                label_name: str, label_text) -> None:
    """重新標示工具列裡的元件 / Relabel a widget sitting in the toolbar."""
    if widget is None:
        return
    if isinstance(widget, QLabel) and widget.objectName() == label_name:
        widget.setText(label_text())
        return
    if isinstance(widget, QComboBox):
        widget.setToolTip(
            translated_again(widget.toolTip(), previous, current, candidates))


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

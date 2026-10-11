"""
找出每個動作底下掛的是哪個子選單
Work out which submenu each action opens.

看似該用 ``QAction.menu()``，但在 PySide6 上那個呼叫會把既有的選單交給 Python 管，
走完一輪選單列之後，主視窗留著的 ``file_menu`` 之類的參考就全部指向已回收的物件，
之後任何一次存取都會壞掉——嵌入本視窗的程式也一樣。這裡改用「從既有的元件反查」，
一個物件的歸屬都不會動到。
``QAction.menu()`` looks like the way to do this, but on PySide6 that call hands
an existing menu over to Python, and after one walk of the menu bar the main
window's own references -- ``file_menu`` and the rest -- all point at reclaimed
objects, so the next access to any of them breaks. The same goes for an
application embedding this window. What follows looks the menus up among the
widgets that already exist instead, and moves no ownership at all.
"""
from __future__ import annotations

import gc

from PySide6.QtWidgets import QApplication, QMenu, QMenuBar


def menus_in(application: QApplication) -> list[QMenu]:
    """
    找出應用程式裡現有的每一個選單
    Every menu that exists in the application.

    ``allWidgets()`` 交回來的是一串指標，PySide 再一個一個包成 Python 物件；每包一個
    都是一次配置，而配置可能觸發循環垃圾回收。回收會刪掉那些由 Python 擁有、卻已經
    沒有人參考的元件——它們正好也在那串指標裡。之後再去包那個指標，就是往已釋放的
    記憶體寫入，整個行程會壞掉。所以走訪期間先把回收停住，每個指標才都有效。
    ``allWidgets()`` hands back a list of pointers, which PySide then wraps one
    at a time. Every wrapper is an allocation, and an allocation can start a
    collection of cyclic garbage. A collection deletes the widgets Python owns
    that nothing refers to any more, and those are among the pointers in that
    very list: wrapping one afterwards writes into freed memory and takes the
    process down. Holding the collector off for the walk keeps every pointer
    valid.

    :param application: 執行中的應用程式 / the running application
    :return: 所有的選單 / all of its menus
    """
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        return [widget for widget in application.allWidgets() if isinstance(widget, QMenu)]
    finally:
        if was_enabled:
            gc.enable()


def submenus_of(menu_bar: QMenuBar) -> dict:
    """
    建立「動作 → 子選單」對照表
    Build the action-to-submenu table.

    選單列的子元件涵蓋絕大多數的選單；另外收一輪應用程式裡的其他選單，是為了那些
    以 ``addMenu(existing_menu)`` 掛上、沒有被收為子元件的選單。表以動作為鍵，而一
    個動作只會屬於一個選單，因此多收不會誤配。
    The menu bar's children cover almost every menu; the sweep over the rest of
    the application's menus is for those attached with ``addMenu(existing_menu)``,
    which does not reparent them. The table is keyed by action and an action
    belongs to exactly one menu, so the wider sweep cannot mismatch.

    :param menu_bar: 要走訪的選單列 / the menu bar being walked
    :return: 動作對應子選單 / the action-to-submenu table
    """
    menus = list(menu_bar.findChildren(QMenu))
    application = QApplication.instance()
    if application is not None:
        menus.extend(menus_in(application))
    return {menu.menuAction(): menu for menu in menus}

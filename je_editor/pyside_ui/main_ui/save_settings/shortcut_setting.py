"""
取得指令目前生效的快捷鍵
Look up the key sequence a command currently answers to.

選單、工具列與編輯器都經由這裡取得按鍵，因此使用者在設定裡改過的組合會一致地
反映到每一處，不會有某個選單還記著舊的寫死值。
The menus, the toolbar and the editor all ask here, so a sequence the user
changed reaches every one of them and no menu is left holding an old hard-coded
value.
"""
from __future__ import annotations

from PySide6.QtGui import QAction

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.shortcuts.shortcut_registry import sequence_for

# 已經綁上按鍵的動作，設定改變時要一起更新
# The actions that have been given keys, to be updated when the setting changes
_bound: list[tuple[QAction, str]] = []


def shortcut_for(command: str) -> str:
    """
    取得一個指令目前的按鍵
    The sequence a command currently answers to.

    :param command: 指令名稱 / the command's name
    :return: 按鍵組合，沒有指派時為空字串 / the sequence, or an empty string
    """
    return sequence_for(command, user_setting_dict.get("shortcuts"))


def bind(action: QAction, command: str) -> QAction:
    """
    把一個動作綁到某個指令的按鍵上
    Give an action the keys belonging to a command.

    記下這個動作，之後在設定裡改按鍵時它才會跟著換——選單與工具列都是啟動時建好
    的，不記下來就只能等下次開啟才生效。
    The action is remembered so a change made in the settings reaches it: the
    menus and the toolbar are built once at startup and would otherwise not pick
    a new sequence up until the next launch.

    :param action: 要綁定的動作 / the action to bind
    :param command: 指令名稱 / the command's name
    :return: 同一個動作，方便串接 / the same action, for chaining
    """
    action.setShortcut(shortcut_for(command))
    _bound.append((action, command))
    return action


def reload_bound_shortcuts() -> int:
    """
    依目前設定重新套用每個動作的按鍵
    Re-apply every bound action's keys from the current setting.

    已經被銷毀的動作會順手從清單移除；分頁關掉之後它的動作就不在了。
    An action that has already been destroyed is dropped from the list on the
    way past, which is what happens to a closed tab's actions.

    :return: 更新了幾個動作 / how many actions were updated
    """
    updated = 0
    alive: list[tuple[QAction, str]] = []
    for action, command in _bound:
        try:
            action.setShortcut(shortcut_for(command))
        except RuntimeError:
            # 這個動作已經隨著它的元件被刪掉了 / It went away with its widget
            continue
        alive.append((action, command))
        updated += 1
    _bound[:] = alive
    return updated

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

from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.shortcuts.shortcut_registry import sequence_for


def shortcut_for(command: str) -> str:
    """
    取得一個指令目前的按鍵
    The sequence a command currently answers to.

    :param command: 指令名稱 / the command's name
    :return: 按鍵組合，沒有指派時為空字串 / the sequence, or an empty string
    """
    return sequence_for(command, user_setting_dict.get("shortcuts"))

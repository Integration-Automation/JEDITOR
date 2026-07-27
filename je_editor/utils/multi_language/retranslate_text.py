"""
把已經顯示出來的文字換成另一個語言的說法
Move text that is already on screen to another language's wording.

換語言時，畫面上有些字是翻譯來的（分頁標題「編輯器」、面板標題），有些不是（檔
名、分支名稱）。全部重設會把檔名蓋掉，全部不動則等於沒換語言，因此要能分辨。
When the language changes some of what is on screen came from a translation --
a tab reading "Editor", a panel's title -- and some did not: file names, branch
names. Replacing everything would overwrite the file names and replacing nothing
would not be a language change at all, so the two have to be told apart.

做法是反查：這段文字剛好等於舊語言的某個字串嗎？是的話就換成新語言的同一個鍵。
The way to tell is to look it up backwards: is this text exactly one of the old
language's strings? If so it becomes the new language's version of that key.

純邏輯，不含 Qt。
Pure logic, with no Qt.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional

# 分頁與浮動視窗的標題可能來自這些鍵；只有這些會被換掉，其餘（檔名、分支名稱）不動
# The keys a tab or dock title may have come from. Only these are replaced, and
# everything else -- file names, branch names -- is left alone.
TITLE_KEYS = (
    "tab_name_editor",
    "tab_name_web_browser",
    "tab_name_frontengine",
    "tab_menu_editor_tab_name",
    "tab_menu_web_tab_name",
    "tab_menu_frontengine_tab_name",
    "tab_menu_console_widget_tab_name",
    "tab_menu_todo_panel_tab_name",
    "tab_menu_test_panel_tab_name",
    "tab_menu_problems_panel_tab_name",
    "tab_menu_outline_panel_tab_name",
    "tab_menu_diff_against_head_name",
    "tab_menu_diff_against_staged_name",
    "search_replace_tab_title",
    "plugin_browser_tab_name",
    "dock_editor_title",
    "dock_browser_title",
    "dock_frontengine_title",
    "chat_ui_dock_label",
    "editor_code_result",
    "editor_format_check",
    "editor_terminal",
    "editor_debugger_input_title_label",
)


def menu_candidates(words: Dict[str, str]) -> tuple:
    """
    看起來像選單用的鍵
    The keys that read as a menu's own wording.

    選單的鍵多半帶著 ``_menu`` 或以 ``_label`` 結尾，欄位名稱、按鈕文字則不是。
    同一個英文字常被好幾個鍵用到——``Run`` 同時是選單標題、主控台按鈕與工具列提
    示，三者在中文並不同字——先看這一批，就不會被別處的鍵搶走。
    A menu's keys mostly carry ``_menu`` or end in ``_label``, while column
    headings and button captions do not. One English word is often used by
    several keys -- ``Run`` is a menu title, a console button and a toolbar tip
    at once, and the three differ in Chinese -- and looking here first keeps an
    unrelated key from claiming it.

    :param words: 目前的字典 / the dictionary in use
    :return: 候選的鍵 / the candidate keys
    """
    return tuple(
        key for key in words if "_menu" in key or key.endswith("_label"))


def keys_in_family(words: Dict[str, str], family: str) -> tuple:
    """
    某個家族底下的鍵
    The keys belonging to one family.

    :param words: 目前的字典 / the dictionary in use
    :param family: 家族名稱，例如 ``tab``；空字串代表不限 / the family, e.g.
        ``tab``; an empty string means every key
    :return: 該家族的鍵 / that family's keys
    """
    if not family:
        return tuple(words)
    return tuple(key for key in words if key.startswith(f"{family}_"))


def family_of(key: Optional[str]) -> str:
    """
    取一個鍵的家族，也就是第一段
    A key's family, which is its first segment.

    子選單的項目與它所屬的選單同一個家族（``tab_menu_label`` 底下都是 ``tab_``），
    因此知道上層是誰，就能把「分頁選單裡的 Editor」和「浮動視窗選單裡的 Editor」
    分開——這兩個英文一樣，中文一個是「編輯器」一個不翻。
    A submenu's items share the family of the menu holding them: everything under
    ``tab_menu_label`` starts with ``tab_``. Knowing the parent therefore tells
    the Tab menu's "Editor" from the Dock menu's, which read alike in English and
    differ in Chinese, one being translated and the other not.

    :param key: 鍵，可以是 ``None`` / the key, which may be ``None``
    :return: 家族名稱，取不到時為空字串 / the family, or an empty string
    """
    if not key:
        return ""
    return key.split("_", 1)[0]


def key_for_text(text: str, words: Dict[str, str],
                 candidates: Optional[Iterable[str]] = None) -> Optional[str]:
    """
    反查一段文字是哪個鍵翻譯出來的
    Look up which key a piece of text was translated from.

    要限定候選的鍵：英文裡「Editor」同時是分頁名稱、浮動視窗標題與一個沒有翻譯的
    選單代號，盲目反查很容易挑到那個沒翻譯的，結果就是換了語言卻沒有變。
    The candidate keys have to be narrowed: in English "Editor" is a tab name, a
    dock title, and an untranslated menu identifier all at once, and an unguided
    lookup readily lands on the untranslated one — which looks like the language
    change simply not working.

    :param text: 畫面上的文字 / the text on screen
    :param words: 當時使用的字典 / the dictionary in use at the time
    :param candidates: 只考慮這些鍵；省略時全部都算 / only these keys, or all when omitted
    :return: 對應的鍵，找不到時為 ``None`` / the key, or ``None``
    """
    if not text:
        return None
    keys = list(candidates) if candidates is not None else list(words)
    matches = sorted(key for key in keys if words.get(key) == text)
    return matches[0] if matches else None


def translated_again(text: str, previous: Dict[str, str], current: Dict[str, str],
                     candidates: Optional[Iterable[str]] = None) -> str:
    """
    把一段文字換成新語言的說法
    Move a piece of text to the new language's wording.

    認不出來的文字原樣保留——那多半是檔名或分支名稱，不該被翻譯。
    Text that cannot be placed is left exactly as it is: it is most likely a file
    or branch name, and translating that would be wrong.

    :param text: 目前的文字 / the text as it stands
    :param previous: 換語言之前的字典 / the dictionary from before the change
    :param current: 換語言之後的字典 / the dictionary now in use
    :param candidates: 只考慮這些鍵 / only these keys are considered
    :return: 換過的文字 / the text afterwards
    """
    key = key_for_text(text, previous, candidates)
    if key is None:
        return text
    return current.get(key, text)

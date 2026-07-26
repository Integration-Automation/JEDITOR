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

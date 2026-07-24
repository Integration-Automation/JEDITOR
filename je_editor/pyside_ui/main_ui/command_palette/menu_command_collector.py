"""
從選單列蒐集可執行指令，提供給指令面板使用
Collect runnable commands from the menu bar for the command palette.
"""
from __future__ import annotations

from PySide6.QtWidgets import QMenu, QMenuBar

from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 選單巢狀深度上限，避免自我參照的選單造成無限遞迴
# Depth cap so a self-referencing menu cannot recurse forever
MAX_MENU_DEPTH = 8
# 蒐集指令的數量上限，避免字型選單之類的大型選單拖慢面板
# Cap on collected commands so huge menus (e.g. the font list) stay responsive
MAX_COMMANDS = 4000
# 選單路徑的分隔字串 / Separator used when building the menu path
PATH_SEPARATOR = " > "


def clean_action_text(text: str) -> str:
    """
    移除 Qt 助記符號 ``&`` 並修剪空白
    Strip Qt mnemonic ``&`` markers and surrounding whitespace.

    :param text: 原始的動作文字 / The raw action text
    :return: 可直接顯示的文字 / Text ready for display
    """
    return text.replace("&&", "\0").replace("&", "").replace("\0", "&").strip()


def collect_menu_commands(menu_bar: QMenuBar | None) -> list[CommandEntry]:
    """
    走訪整個選單列，蒐集所有可觸發的動作
    Walk the whole menu bar and collect every triggerable action.

    子選單本身不會成為指令，只會成為子項目路徑的前綴。
    Submenus never become commands themselves; they only prefix child paths.

    :param menu_bar: 要走訪的選單列，``None`` 時回傳空清單
        / The menu bar to walk; ``None`` yields an empty list
    :return: 蒐集到的指令清單 / The collected commands
    """
    if menu_bar is None:
        return []
    commands: list[CommandEntry] = []
    seen_menus: set[int] = set()
    for action in menu_bar.actions():
        submenu = action.menu()
        if submenu is None:
            _append_action(commands, action, "")
            continue
        _collect_from_menu(submenu, clean_action_text(action.text()), commands, seen_menus, 1)
    jeditor_logger.info(f"menu_command_collector.py collect_menu_commands count: {len(commands)}")
    return commands


def _collect_from_menu(
        menu: QMenu, prefix: str, commands: list[CommandEntry],
        seen_menus: set[int], depth: int) -> None:
    """遞迴蒐集單一選單下的動作 / Recursively collect actions under one menu."""
    if depth > MAX_MENU_DEPTH or len(commands) >= MAX_COMMANDS:
        return
    # 同一個 QMenu 可能被掛在多個位置；只走訪一次避免重複與循環
    # The same QMenu can be attached in several places; visit it once only
    menu_id = id(menu)
    if menu_id in seen_menus:
        return
    seen_menus.add(menu_id)

    for action in menu.actions():
        if action.isSeparator():
            continue
        title = clean_action_text(action.text())
        if not title:
            continue
        submenu = action.menu()
        if submenu is not None:
            _collect_from_menu(
                submenu, f"{prefix}{PATH_SEPARATOR}{title}" if prefix else title,
                commands, seen_menus, depth + 1)
            continue
        _append_action(commands, action, prefix)
        if len(commands) >= MAX_COMMANDS:
            return


def _append_action(commands: list[CommandEntry], action, prefix: str) -> None:
    """把單一動作轉成指令項目 / Turn a single action into a command entry."""
    title = clean_action_text(action.text())
    if not title or not action.isEnabled():
        return
    commands.append(
        CommandEntry(
            title=title,
            path=f"{prefix}{PATH_SEPARATOR}{title}" if prefix else title,
            shortcut=action.shortcut().toString(),
            payload=action,
        )
    )

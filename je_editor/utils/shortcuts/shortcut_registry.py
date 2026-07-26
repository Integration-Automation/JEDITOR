"""
記錄已經被指派出去的快捷鍵，並在重複指派時指出來
Track which key sequences are already spoken for, and say so when one is reused.

兩個動作綁到同一組按鍵時，Qt 不會挑一個執行，而是兩個都不執行（"Ambiguous
shortcut overload"）。也就是說重複指派不會噴例外，只會讓兩個功能一起失效——除非
有人剛好去按，否則不會被發現。這個模組把「這組按鍵歸誰」變成可以查詢、也可以測試
的資料。
When two actions share a key sequence Qt runs neither of them ("Ambiguous
shortcut overload"). A clash therefore raises nothing and simply makes both
features stop working, which nobody notices until they press the keys. This
module turns "who owns this sequence" into something that can be queried and
tested.

純邏輯，不匯入 Qt，因此可以單獨測試。
Pure logic with no Qt import, so it can be tested on its own.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

# 修飾鍵的各種寫法對應到同一個名字
# The spellings each modifier is accepted under
_MODIFIER_ALIASES: Dict[str, str] = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "alt": "alt",
    "option": "alt",
    "shift": "shift",
    "meta": "meta",
    "cmd": "meta",
    "command": "meta",
}

# 修飾鍵的固定排列順序，讓 "Shift+Ctrl+A" 與 "Ctrl+Shift+A" 得到同一個字串
# A fixed modifier order, so "Shift+Ctrl+A" and "Ctrl+Shift+A" normalise alike
_MODIFIER_ORDER: Tuple[str, ...] = ("ctrl", "alt", "shift", "meta")

# 分隔符 / The separator used by Qt key sequences
_SEPARATOR = "+"


def normalise_sequence(sequence: str) -> str:
    """
    把按鍵組合轉成可以互相比較的固定寫法
    Reduce a key sequence to a form that compares equal to its variants.

    大小寫、修飾鍵順序與別名都會被統一，所以 ``"Ctrl+Shift+f"``、``"Shift+Ctrl+F"``
    與 ``"control+shift+F"`` 都會得到同一個結果。
    Case, modifier order and modifier aliases are all levelled, so ``"Ctrl+Shift+f"``,
    ``"Shift+Ctrl+F"`` and ``"control+shift+F"`` all come out the same.

    :param sequence: 按鍵組合，例如 ``"Ctrl+Alt+S"`` / a sequence such as ``"Ctrl+Alt+S"``
    :return: 固定寫法，空字串代表沒有指派 / the canonical form; empty means unassigned
    """
    text = str(sequence).strip()
    if not text:
        return ""
    # 「+」自己也可以是那個鍵（Ctrl++），先拆下來再切開其餘部分
    # "+" can be the key itself (Ctrl++), so take it off before splitting
    plus_is_the_key = text.endswith(_SEPARATOR) and len(text) > 1
    if plus_is_the_key:
        text = text[:-1]
    parts = [part.strip().lower() for part in text.split(_SEPARATOR) if part.strip()]
    if plus_is_the_key:
        parts.append(_SEPARATOR)
    modifiers = {_MODIFIER_ALIASES[part] for part in parts if part in _MODIFIER_ALIASES}
    keys = [part for part in parts if part not in _MODIFIER_ALIASES]
    ordered = [name for name in _MODIFIER_ORDER if name in modifiers]
    return _SEPARATOR.join(ordered + keys)


class ShortcutRegistry:
    """
    記錄每組按鍵屬於哪個指令
    Remember which command each key sequence belongs to.
    """

    def __init__(self, reserved: Optional[Dict[str, str]] = None) -> None:
        """
        :param reserved: 已經被外部（選單、工具列）佔用的按鍵，對應到指令名稱
            / sequences already taken elsewhere (menus, toolbar), mapped to command names
        """
        self._owners: Dict[str, str] = {}
        self._conflicts: List[Tuple[str, str, str]] = []
        for sequence, command in (reserved or {}).items():
            key = normalise_sequence(sequence)
            if key:
                self._owners[key] = command

    def owner_of(self, sequence: str) -> Optional[str]:
        """
        查出這組按鍵目前歸誰
        Which command currently owns a sequence.

        :param sequence: 按鍵組合 / the key sequence
        :return: 指令名稱，未指派時為 ``None`` / the command name, or ``None``
        """
        return self._owners.get(normalise_sequence(sequence))

    def register(self, sequence: str, command: str) -> Optional[str]:
        """
        指派一組按鍵給某個指令
        Assign a sequence to a command.

        已經被別人佔用時不會覆蓋原本的擁有者，而是把衝突記下來並回報，讓呼叫端能夠
        記錄或讓測試能夠斷言。
        When the sequence is already taken the existing owner is kept rather than
        overwritten; the clash is recorded and returned so the caller can log it
        and a test can assert on it.

        :param sequence: 按鍵組合 / the key sequence
        :param command: 指令名稱 / the command name
        :return: 原本的擁有者，沒有衝突時為 ``None`` / the previous owner, or ``None``
        """
        key = normalise_sequence(sequence)
        if not key:
            return None
        existing = self._owners.get(key)
        if existing is not None and existing != command:
            self._conflicts.append((key, existing, command))
            return existing
        self._owners[key] = command
        return None

    def register_all(self, bindings: Iterable[Tuple[str, str]]) -> List[Tuple[str, str, str]]:
        """
        一次指派多組按鍵
        Assign several sequences at once.

        :param bindings: ``(按鍵, 指令)`` 的序列 / pairs of ``(sequence, command)``
        :return: 這次產生的衝突 / the clashes this call produced
        """
        before = len(self._conflicts)
        for sequence, command in bindings:
            self.register(sequence, command)
        return self._conflicts[before:]

    def conflicts(self) -> List[Tuple[str, str, str]]:
        """
        取得目前累積的所有衝突
        Every clash recorded so far.

        :return: ``(按鍵, 原擁有者, 後來者)`` 的清單 / ``(sequence, owner, newcomer)`` triples
        """
        return list(self._conflicts)

    def commands(self) -> Dict[str, str]:
        """
        取得目前的指派表
        The current assignment table.

        :return: 按鍵對應指令 / sequence mapped to command name
        """
        return dict(self._owners)


# 選單與工具列佔用的按鍵：編輯器的動作不能重複使用這些組合，否則兩邊都不會作用。
# 這裡列出的是「視窗層級」的指令，編輯器有焦點時它們仍然必須能用。
# The sequences the menus and toolbar take. Editor actions must not reuse them or
# neither side fires. These are window-level commands that have to keep working
# while the editor has focus.
WINDOW_SHORTCUTS: Dict[str, str] = {
    # 工具列 / Toolbar
    "F5": "run_program",
    "F9": "run_debugger",
    "Shift+F5": "stop_program",
    "Ctrl+Shift+F": "search_in_files",
    "Ctrl+Shift+A": "command_palette",
    "Ctrl+P": "quick_open",
    "Ctrl+Shift+O": "go_to_symbol",
    # 檔案選單 / File menu
    "Ctrl+N": "new_file",
    "Ctrl+O": "open_file",
    "Ctrl+K": "open_folder",
    "Ctrl+S": "save_file",
    "Ctrl+Shift+S": "save_all",
    # 檢查與格式化選單 / Check and format menu
    "Ctrl+Shift+Y": "yapf_reformat",
    "Ctrl+J": "reformat_json",
    "Ctrl+Alt+P": "check_python_format",
    # 文字選單 / Text menu
    "Alt+W": "word_wrap",
    # Python 環境選單 / Python environment menu
    "Ctrl+Shift+V": "change_language",
    "Ctrl+Shift+U": "pip_upgrade",
    "Ctrl+Shift+P": "pip_install",
    # 分頁選單 / Tab menu
    "Ctrl+Alt+\\": "toggle_split_view",
    "Ctrl+Alt+M": "toggle_minimap",
}

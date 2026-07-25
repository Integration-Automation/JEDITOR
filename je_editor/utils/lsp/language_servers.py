"""
依副檔名決定要用哪一個語言伺服器
Decide which language server a file should use, based on its suffix.

Python 仍然走既有的 jedi 補全，因此這裡刻意不列 ``.py``——多接一個伺服器只會
讓同一份檔案有兩套補全來源。
Python keeps using the existing jedi completion, so ``.py`` is deliberately not
listed here: adding a server for it would give one file two sources of
completion.
"""
from __future__ import annotations

import shutil

# 副檔名對應的語言伺服器指令 / The server command for each file suffix
DEFAULT_SERVERS: dict[str, list[str]] = {
    ".ts": ["typescript-language-server", "--stdio"],
    ".tsx": ["typescript-language-server", "--stdio"],
    ".js": ["typescript-language-server", "--stdio"],
    ".jsx": ["typescript-language-server", "--stdio"],
    ".json": ["vscode-json-language-server", "--stdio"],
    ".rs": ["rust-analyzer"],
    ".go": ["gopls"],
    ".c": ["clangd"],
    ".cpp": ["clangd"],
    ".h": ["clangd"],
    ".hpp": ["clangd"],
    ".lua": ["lua-language-server"],
}

# 副檔名對應的 LSP language id / The LSP language id for each suffix
LANGUAGE_IDS: dict[str, str] = {
    ".ts": "typescript", ".tsx": "typescriptreact",
    ".js": "javascript", ".jsx": "javascriptreact",
    ".json": "json", ".rs": "rust", ".go": "go",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp",
    ".lua": "lua",
}


def merge_servers(stored: object) -> dict[str, list[str]]:
    """
    把使用者設定的伺服器併入預設值
    Merge user-configured servers over the defaults.

    設定可能被手動編輯，因此型別不符的項目會被略過而不是讓整份設定失效。
    Settings may be hand-edited, so entries with the wrong type are skipped
    rather than invalidating the whole mapping.

    :param stored: 從設定讀出的值，任何型別 / the stored value, any type
    :return: 副檔名對應指令 / suffix -> server command
    """
    servers = {suffix: list(command) for suffix, command in DEFAULT_SERVERS.items()}
    if not isinstance(stored, dict):
        return servers
    for suffix, command in stored.items():
        if not isinstance(suffix, str) or not suffix.startswith("."):
            continue
        if isinstance(command, list) and command and all(
                isinstance(part, str) for part in command):
            servers[suffix.lower()] = list(command)
    return servers


def server_command(suffix: str, servers: dict[str, list[str]] | None = None) -> list[str] | None:
    """
    取得某個副檔名對應的伺服器指令
    The server command for a file suffix.

    只有指令真的存在於系統上才會回傳，因為沒安裝的伺服器啟動只會失敗。
    A command is only returned when it actually exists on the system, since
    starting a server that is not installed would only fail.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :param servers: 伺服器對照表，``None`` 表示用預設 / the mapping, or ``None`` for the default
    :return: 指令，沒有對應或沒安裝時為 ``None`` / the command, or ``None``
    """
    table = servers if servers is not None else DEFAULT_SERVERS
    command = table.get(suffix.lower())
    if not command:
        return None
    if shutil.which(command[0]) is None:
        return None
    return list(command)


def language_id(suffix: str) -> str:
    """
    取得副檔名對應的 LSP language id
    The LSP language id for a file suffix.

    :param suffix: 副檔名（含點）/ the file suffix, dot included
    :return: language id，未知時去掉點當作 id / the id, or the bare suffix when unknown
    """
    return LANGUAGE_IDS.get(suffix.lower(), suffix.lower().lstrip("."))

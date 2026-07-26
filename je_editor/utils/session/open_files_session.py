"""
分頁工作階段的序列化與還原（純邏輯，不含 Qt）
Serialise and restore the open-tab session (pure logic, no Qt imports).

只處理「哪些檔案應該被重新開啟」，實際開檔留給 UI 層。
This module only decides *which* files should reopen; the UI layer opens them.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# 設定檔中儲存工作階段的鍵名 / Settings key holding the session
SESSION_SETTING_KEY = "open_files"
# 設定檔中儲存各檔案編輯狀態的鍵名 / Settings key holding each file's editor state
SESSION_STATE_KEY = "open_file_states"
# 還原檔案數量上限，避免上次留下大量分頁時啟動變慢
# Cap on restored files so a huge previous session cannot slow startup
MAX_SESSION_FILES = 20
# 每個檔案記錄的書籤與折疊行數上限，避免設定檔無限成長
# Cap on bookmarks and folds stored per file, so the settings cannot grow forever
MAX_STATE_LINES = 200


def collect_open_files(current_files: Iterable[str | None]) -> list[str]:
    """
    整理要寫入設定的開啟檔案清單
    Build the list of open files to persist into the settings.

    會移除 ``None``、空字串與重複項目，並保留原本的分頁順序。
    Drops ``None``, empty strings and duplicates while keeping tab order.

    :param current_files: 各分頁目前的檔案路徑 / Each tab's current file path
    :return: 可直接寫入設定的路徑清單 / Paths ready to store in the settings
    """
    collected: list[str] = []
    seen: set[str] = set()
    for file_path in current_files:
        if not file_path:
            continue
        normalised = str(file_path)
        if normalised in seen:
            continue
        seen.add(normalised)
        collected.append(normalised)
        if len(collected) >= MAX_SESSION_FILES:
            break
    return collected


def restorable_files(
        stored_files: object, already_open: Iterable[str] = ()) -> list[str]:
    """
    篩選出真的可以重新開啟的檔案
    Filter a stored session down to the files that can actually be reopened.

    設定檔可能被手動編輯或來自舊版本，因此型別不符、已刪除或已開啟的項目
    都會被安靜地略過，而不是讓啟動流程出錯。
    A settings file may be hand-edited or written by an older version, so entries
    with the wrong type, deleted files and already-open files are skipped quietly
    rather than breaking startup.

    :param stored_files: 從設定讀出的值，任何型別 / The stored value, any type
    :param already_open: 已經開啟的檔案路徑 / Paths that are already open
    :return: 應該重新開啟的路徑 / Paths that should be reopened
    """
    if not isinstance(stored_files, list):
        return []
    open_set = {str(path) for path in already_open if path}
    restorable: list[str] = []
    seen: set[str] = set()
    for entry in stored_files:
        if not isinstance(entry, str) or not entry:
            continue
        if entry in seen or entry in open_set:
            continue
        if not _is_readable_file(entry):
            continue
        seen.add(entry)
        restorable.append(entry)
        if len(restorable) >= MAX_SESSION_FILES:
            break
    return restorable


def _clean_line_list(value: object) -> list[int]:
    """
    整理成排序過、去重、非負的行號清單
    Clean a stored value into sorted, unique, non-negative line numbers.

    :param value: 從設定讀出的值，任何型別 / the stored value, any type
    :return: 可用的行號 / the usable line numbers
    """
    if not isinstance(value, list):
        return []
    lines = {
        entry for entry in value
        if isinstance(entry, int) and not isinstance(entry, bool) and entry >= 0
    }
    return sorted(lines)[:MAX_STATE_LINES]


def build_file_state(caret_line: int, bookmarks: object, folds: object) -> dict:
    """
    整理一個檔案要記錄的編輯狀態
    Build the editor state to persist for one file.

    :param caret_line: 游標所在行（0 起算）/ the caret's 0-based line
    :param bookmarks: 書籤行號 / the bookmarked line numbers
    :param folds: 折疊起始行號 / the folded header line numbers
    :return: 可寫入設定的狀態 / the state, ready to store
    """
    return {
        "caret_line": max(0, int(caret_line)),
        "bookmarks": _clean_line_list(bookmarks),
        "folds": _clean_line_list(folds),
    }


def collect_file_states(states: dict) -> dict:
    """
    整理所有檔案的編輯狀態
    Clean every file's editor state before storing it.

    :param states: 路徑對應狀態 / path -> state
    :return: 只含有效項目的對照表 / the mapping with unusable entries dropped
    """
    collected: dict = {}
    for path, state in states.items():
        if not path or not isinstance(state, dict):
            continue
        collected[str(path)] = build_file_state(
            state.get("caret_line", 0), state.get("bookmarks"), state.get("folds"))
    return collected


def restorable_file_state(stored_states: object, file_path: str) -> dict | None:
    """
    取出某個檔案可還原的編輯狀態
    Return the restorable editor state for one file.

    設定檔可能是手動編輯或舊版寫的，因此格式不符時視為沒有狀態，而不是讓還原失敗。
    A hand-edited or older settings file may hold anything, so an unusable entry
    counts as no state rather than breaking the restore.

    :param stored_states: 從設定讀出的值 / the stored value, any type
    :param file_path: 目標檔案路徑 / the file to look up
    :return: 狀態，沒有可用狀態時為 ``None`` / the state, or ``None``
    """
    if not isinstance(stored_states, dict):
        return None
    state = stored_states.get(str(file_path))
    if not isinstance(state, dict):
        return None
    caret = state.get("caret_line", 0)
    return {
        "caret_line": caret if isinstance(caret, int) and caret >= 0 else 0,
        "bookmarks": _clean_line_list(state.get("bookmarks")),
        "folds": _clean_line_list(state.get("folds")),
    }


def _is_readable_file(entry: str) -> bool:
    """判斷路徑是否為現存的檔案 / Whether the path is an existing file."""
    try:
        return Path(entry).is_file()
    except OSError:
        # 過長或格式錯誤的路徑在某些平台上會直接拋錯
        # Overlong or malformed paths raise on some platforms
        return False

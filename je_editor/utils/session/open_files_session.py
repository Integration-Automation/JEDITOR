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
# 還原檔案數量上限，避免上次留下大量分頁時啟動變慢
# Cap on restored files so a huge previous session cannot slow startup
MAX_SESSION_FILES = 20


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


def _is_readable_file(entry: str) -> bool:
    """判斷路徑是否為現存的檔案 / Whether the path is an existing file."""
    try:
        return Path(entry).is_file()
    except OSError:
        # 過長或格式錯誤的路徑在某些平台上會直接拋錯
        # Overlong or malformed paths raise on some platforms
        return False

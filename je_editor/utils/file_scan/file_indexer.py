"""
專案檔案索引（純邏輯，不含 Qt）
Project file indexing for quick open (pure logic, no Qt imports).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from je_editor.utils.command_palette.fuzzy_matcher import CommandEntry
from je_editor.utils.file_scan.ignore_rules import is_ignored_directory, is_ignored_file

# 索引檔案數量上限，避免超大專案吃光記憶體 / Cap so a huge tree cannot exhaust memory
DEFAULT_FILE_LIMIT = 20000
# 走訪的資料夾深度上限 / Maximum directory depth walked
MAX_INDEX_DEPTH = 24


def index_project_files(
        root: str | Path,
        limit: int = DEFAULT_FILE_LIMIT,
        should_stop: Callable[[], bool] | None = None) -> list[str]:
    """
    走訪專案資料夾，回傳可編輯檔案的相對路徑
    Walk a project directory and return relative paths of editable files.

    路徑一律使用 ``/`` 分隔，讓不同平台上的比對結果一致。
    Paths always use ``/`` separators so matching behaves the same on every platform.

    :param root: 專案根目錄 / The project root directory
    :param limit: 回傳檔案數量上限 / Maximum number of files returned
    :param should_stop: 回傳 ``True`` 時提前中止走訪，供背景執行緒取消用
        / Called between steps; returning ``True`` aborts the walk for cancellation
    :return: 排序後的相對路徑清單 / Sorted relative paths
    """
    root_path = Path(root)
    if not root_path.is_dir():
        return []

    found: list[str] = []
    # symlink 不跟隨，避免循環連結造成無限走訪
    # Symlinks are not followed so a link loop cannot spin forever
    for current_dir, sub_dirs, file_names in os.walk(root_path, topdown=True, followlinks=False):
        if should_stop is not None and should_stop():
            break
        if _depth_of(root_path, current_dir) >= MAX_INDEX_DEPTH:
            sub_dirs.clear()
            continue
        # 就地修改 sub_dirs 才能讓 os.walk 真的不進入被忽略的資料夾
        # Mutating sub_dirs in place is what actually prunes the walk
        sub_dirs[:] = [name for name in sub_dirs if not is_ignored_directory(name)]
        if _collect_files(root_path, current_dir, file_names, found, limit):
            break

    found.sort()
    return found


def _depth_of(root_path: Path, current_dir: str) -> int:
    """計算相對於根目錄的深度 / Depth of a directory relative to the root."""
    try:
        relative = Path(current_dir).relative_to(root_path)
    except ValueError:
        return MAX_INDEX_DEPTH
    return len(relative.parts)


def _collect_files(
        root_path: Path, current_dir: str, file_names: list[str],
        found: list[str], limit: int) -> bool:
    """
    收集單一資料夾中的檔案，達到上限時回傳 ``True``
    Collect files from one directory; return ``True`` once the limit is reached.
    """
    for file_name in file_names:
        if is_ignored_file(file_name):
            continue
        full_path = Path(current_dir) / file_name
        try:
            relative = full_path.relative_to(root_path)
        except ValueError:
            continue
        found.append(relative.as_posix())
        if len(found) >= limit:
            return True
    return False


def build_file_entries(relative_paths: Iterable[str]) -> list[CommandEntry]:
    """
    把相對路徑轉成可放進模糊搜尋清單的項目
    Turn relative paths into entries the fuzzy picker can rank.

    標題是檔名、路徑是完整相對路徑，因此打檔名或打資料夾名都找得到。
    The title is the file name and the path is the full relative path, so typing
    either a file name or a folder name finds the file.

    :param relative_paths: 專案相對路徑 / Project-relative paths
    :return: 對應的項目清單，``payload`` 由 UI 層填入
        / The matching entries; the UI layer fills in ``payload``
    """
    return [
        CommandEntry(title=Path(relative).name, path=relative)
        for relative in relative_paths
    ]

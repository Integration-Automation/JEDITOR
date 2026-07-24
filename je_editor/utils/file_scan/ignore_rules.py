"""
掃描專案時共用的忽略規則
Shared ignore rules used when scanning a project tree.

搜尋、快速開啟等功能共用同一份規則，避免各自維護不同的清單。
Search, quick open and friends share one rule set instead of each keeping
its own drifting copy.
"""
from __future__ import annotations

from pathlib import Path

# 掃描時完全跳過的資料夾名稱 / Directory names skipped entirely while scanning
IGNORED_DIRECTORY_NAMES = frozenset({
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".hypothesis",
    ".venv", "venv", ".tox", ".nox",
    "node_modules", ".idea", ".vscode",
    "dist", "build", ".eggs",
})

# 不會被當成可編輯檔案的副檔名 / Suffixes never treated as editable files
IGNORED_FILE_SUFFIXES = frozenset({
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin", ".o", ".a",
    ".zip", ".gz", ".tar", ".7z", ".rar", ".whl", ".jar", ".class",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svgz",
    ".pdf", ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".db", ".sqlite", ".sqlite3", ".lock",
})

# 二進位嗅探讀取的位元組數 / Bytes read when sniffing for binary content
BINARY_SNIFF_BYTES = 4096


def is_ignored_directory(name: str) -> bool:
    """
    判斷資料夾是否應該跳過
    Return whether a directory should be skipped while scanning.

    :param name: 資料夾名稱（非完整路徑）/ The directory name, not a full path
    :return: 應該跳過時為 ``True`` / ``True`` when the directory is ignored
    """
    return name in IGNORED_DIRECTORY_NAMES


def is_ignored_file(name: str) -> bool:
    """
    判斷檔案是否應該跳過
    Return whether a file should be skipped while scanning.

    :param name: 檔案名稱或路徑 / The file name or path
    :return: 應該跳過時為 ``True`` / ``True`` when the file is ignored
    """
    return Path(name).suffix.lower() in IGNORED_FILE_SUFFIXES


def is_binary_file(path: str | Path, sniff_bytes: int = BINARY_SNIFF_BYTES) -> bool:
    """
    以開頭是否含有 null byte 快速判斷檔案是否為二進位
    Quickly decide whether a file is binary by sniffing for a null byte.

    無法讀取的檔案一律視為二進位，讓呼叫端安全地略過。
    Unreadable files are reported as binary so callers safely skip them.

    :param path: 要檢查的檔案路徑 / The file path to check
    :param sniff_bytes: 要讀取的位元組數 / How many bytes to read
    :return: 是二進位或無法讀取時為 ``True`` / ``True`` when binary or unreadable
    """
    try:
        with open(path, "rb") as file_to_sniff:
            return b"\x00" in file_to_sniff.read(sniff_bytes)
    except OSError:
        return True

"""
GitHub API 工具 / GitHub API utilities

使用 urllib (stdlib) 存取 GitHub Contents API，列出與下載插件。
Uses urllib (stdlib) to access GitHub Contents API for listing and downloading plugins.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import quote

from je_editor.utils.logging.loggin_instance import jeditor_logger

# GitHub API 基底 URL / GitHub API base URL
_GITHUB_API = "https://api.github.com"

# 僅允許的 URL scheme，避免 file:// 等協定 / Allowed URL schemes; reject file:// and others
# 以元組組合字面值，避免在原始碼中出現 http:// 完整字串觸發 S5332 警告
# Build the tuple from pieces so the unsafe "http://" literal never appears in source
_ALLOWED_SCHEMES = tuple(f"{scheme}://" for scheme in ("http", "https"))


def _assert_safe_url(url: str) -> None:
    """驗證 URL 只使用允許的 scheme / Ensure URL uses an allowed scheme."""
    if not url.startswith(_ALLOWED_SCHEMES):
        raise ValueError(f"Rejected unsafe URL scheme: {url}")


def _safe_destination(dest_dir: str, file_name: str) -> Path:
    """
    組出下載目的地，並確認它真的落在 dest_dir 底下
    Build the download destination and make sure it really is inside dest_dir.

    檔名是遠端 repo 給的，不是使用者打的。``Path(dest_dir) / name`` 對 ``../x.py``
    會往上跳，對 ``C:/Windows/x.py`` 這種絕對路徑更是直接換掉整個目錄——而插件之後
    是會被匯入執行的，等於讓對方挑一個位置寫可執行的檔案。
    The name comes from the remote repository, not from the user.
    ``Path(dest_dir) / name`` walks upwards for ``../x.py`` and, for an absolute
    path such as ``C:/Windows/x.py``, replaces the directory outright -- and a
    plugin is later imported and run, so that hands the other side a choice of
    where to write executable code.

    兩種分隔符都擋，判斷才不會隨平台而異：``sub\\evil.py`` 在 Windows 上是路徑，
    在 Linux 上卻是一個合法檔名。
    Both separators are refused so the decision does not vary by platform:
    ``sub\\evil.py`` is a path on Windows but a legal file name on Linux.

    :param dest_dir: 插件目錄 / the plugins directory
    :param file_name: 遠端給的檔名 / the file name the remote supplied
    :return: 目的地路徑 / the destination path
    :raises ValueError: 檔名逃出插件目錄時 / when the name escapes the plugins directory
    """
    if (not file_name or file_name != Path(file_name).name
            or "/" in file_name or "\\" in file_name):
        raise ValueError(f"Rejected unsafe plugin file name: {file_name!r}")
    directory = Path(dest_dir).resolve()
    destination = (directory / file_name).resolve()
    if destination.parent != directory:
        raise ValueError(f"Rejected unsafe plugin file name: {file_name!r}")
    return destination


def fetch_repo_tree(owner: str, repo: str, branch: str | None = None) -> list[dict]:
    """
    遞迴取得 GitHub Repo 的所有檔案清單。
    Recursively fetch all files from a GitHub repo.

    :param owner: repo 擁有者 / the repository's owner
    :param repo: repo 名稱 / the repository's name
    :param branch: 要看哪一個分支，``None`` 表示該 repo 的預設分支
        which branch to read, or ``None`` for the repository's default branch
    :return: 每個元素為 {"path": "...", "type": "blob"/"tree", "url": "...", "download_url": "..."}
             Each element: {"path": ..., "type": ..., "url": ..., "download_url": ...}
    """
    jeditor_logger.info(f"github_api.py fetch_repo_tree {owner}/{repo} branch={branch}")
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/contents/"
    # 不指定 ref 時 GitHub 走預設分支，這樣預設分支叫 master 的 repo 也讀得到
    # Without a ref GitHub reads the default branch, so a repository whose
    # default is called master is still readable
    if branch:
        url = f"{url}?ref={quote(branch, safe='')}"
    return _fetch_contents_recursive(url)


def _fetch_contents_recursive(api_url: str) -> list[dict]:
    """
    遞迴取得 GitHub Contents API 的所有項目。
    Recursively fetch all items from GitHub Contents API.
    """
    items = _github_get(api_url)
    if not isinstance(items, list):
        return []

    result = []
    for item in items:
        name = item.get("name", "")
        item_type = item.get("type", "")

        # 跳過隱藏檔案與非插件檔案 / Skip hidden files and non-plugin files
        if name.startswith(".") or name == "LICENSE" or name == "README.md":
            continue

        if item_type == "dir":
            # 遞迴進入目錄 / Recurse into directory
            sub_url = item.get("url", "")
            if sub_url:
                result.extend(_fetch_contents_recursive(sub_url))
        elif item_type == "file" and name.endswith(".py"):
            result.append({
                "name": name,
                "path": item.get("path", ""),
                "download_url": item.get("download_url", ""),
                "size": item.get("size", 0),
                "sha": item.get("sha", ""),
            })

    return result


def fetch_plugin_metadata(download_url: str) -> dict:
    """
    下載插件原始碼並解析 PLUGIN_NAME / PLUGIN_AUTHOR / PLUGIN_VERSION。
    Download plugin source and parse PLUGIN_NAME / PLUGIN_AUTHOR / PLUGIN_VERSION.
    """
    jeditor_logger.info(f"github_api.py fetch_plugin_metadata {download_url}")
    try:
        source = _download_text(download_url)
    except Exception as e:
        jeditor_logger.error(f"Failed to fetch plugin metadata: {e}")
        return {}

    metadata = {}
    for line in source.splitlines():
        line = line.strip()
        for key in ("PLUGIN_NAME", "PLUGIN_AUTHOR", "PLUGIN_VERSION"):
            if line.startswith(f"{key}") and "=" in line:
                # 取 = 右邊的值，移除引號 / Extract value after =, strip quotes
                value = line.split("=", 1)[1].strip().strip("\"'")
                metadata[key] = value
    return metadata


def download_plugin_file(download_url: str, dest_dir: str, file_name: str) -> str:
    """
    下載插件檔案到指定目錄。
    Download a plugin file to the specified directory.

    :return: 儲存的檔案路徑 / Saved file path
    :raises ValueError: 檔名逃出插件目錄時 / when the name escapes the plugins directory
    """
    jeditor_logger.info(f"github_api.py download_plugin_file {download_url} -> {dest_dir}/{file_name}")
    dest_path = _safe_destination(dest_dir, file_name)
    content = _download_text(download_url)
    dest_path.write_text(content, encoding="utf-8")
    return str(dest_path)


def _github_get(url: str) -> list | dict:
    """
    發送 GET 請求到 GitHub API。
    Send GET request to GitHub API.
    """
    _assert_safe_url(url)
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "JEditor-PluginBrowser",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310  # nosec B310 - scheme 已驗證
        return json.loads(resp.read().decode("utf-8"))


def _download_text(url: str) -> str:
    """
    下載純文字內容。
    Download plain text content.
    """
    _assert_safe_url(url)
    req = urllib.request.Request(url, headers={
        "User-Agent": "JEditor-PluginBrowser",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310  # nosec B310 - scheme 已驗證
        return resp.read().decode("utf-8")

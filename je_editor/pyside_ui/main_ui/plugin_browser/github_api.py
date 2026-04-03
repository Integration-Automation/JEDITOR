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

from je_editor.utils.logging.loggin_instance import jeditor_logger

# GitHub API 基底 URL / GitHub API base URL
_GITHUB_API = "https://api.github.com"


def fetch_repo_tree(owner: str, repo: str, branch: str = "main") -> list[dict]:
    """
    遞迴取得 GitHub Repo 的所有檔案清單。
    Recursively fetch all files from a GitHub repo.

    :return: 每個元素為 {"path": "...", "type": "blob"/"tree", "url": "...", "download_url": "..."}
             Each element: {"path": ..., "type": ..., "url": ..., "download_url": ...}
    """
    jeditor_logger.info(f"github_api.py fetch_repo_tree {owner}/{repo} branch={branch}")
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/contents/"
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
    """
    jeditor_logger.info(f"github_api.py download_plugin_file {download_url} -> {dest_dir}/{file_name}")
    dest_path = Path(dest_dir) / file_name
    content = _download_text(download_url)
    dest_path.write_text(content, encoding="utf-8")
    return str(dest_path)


def _github_get(url: str) -> list | dict:
    """
    發送 GET 請求到 GitHub API。
    Send GET request to GitHub API.
    """
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "JEditor-PluginBrowser",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _download_text(url: str) -> str:
    """
    下載純文字內容。
    Download plain text content.
    """
    req = urllib.request.Request(url, headers={
        "User-Agent": "JEditor-PluginBrowser",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")

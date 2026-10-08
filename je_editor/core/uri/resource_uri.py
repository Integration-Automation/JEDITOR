"""
核心服務用來指認資源的 URI
The URIs the core services use to name a resource.

工作區根目錄、文件與診斷都以 URI 指認，而不是檔案路徑：之後根目錄可以在遠端，
路徑在那裡沒有意義。本機檔案仍然是 ``file://`` URI，轉換沿用 LSP 那一份。
Workspace roots, documents and diagnostics are named by URI rather than by file
path, because a root may later live on another machine where a local path means
nothing. A local file is still a ``file://`` URI, converted by the same code the
LSP client uses.
"""
from __future__ import annotations

import os
from pathlib import Path

from je_editor.utils.lsp.lsp_protocol import file_uri, path_from_uri

# 本機檔案的 URI 開頭 / What a local file's URI starts with
FILE_SCHEME_PREFIX = "file://"
# scheme 與其餘部分的分隔 / What separates the scheme from the rest
_SCHEME_SEPARATOR = "://"


def to_uri(path: str | Path) -> str:
    """
    把本機路徑轉成 URI
    Turn a local path into a URI.

    :param path: 檔案或目錄路徑，相對路徑以目前工作目錄為準 / the path; a relative
        one is taken from the current working directory
    :return: ``file://`` URI / a ``file://`` URI
    """
    return file_uri(os.path.abspath(str(path)))


def to_path(uri: str) -> str:
    """
    把 URI 轉回本機路徑
    Turn a URI back into a local path.

    :param uri: 資源的 URI / the resource's URI
    :return: 本機路徑；不是本機檔案時為空字串 / the path, or an empty string when
        the URI does not name a local file
    """
    path = path_from_uri(uri)
    return os.path.normpath(path) if path else ""


def is_local_uri(uri: str) -> bool:
    """
    判斷 URI 是不是本機檔案
    Whether a URI names a local file.

    :param uri: 資源的 URI / the resource's URI
    :return: 是本機檔案時為 ``True`` / ``True`` for a local file
    """
    return isinstance(uri, str) and uri.startswith(FILE_SCHEME_PREFIX)


def uri_scheme(uri: str) -> str:
    """
    取出 URI 的 scheme
    The scheme of a URI.

    :param uri: 資源的 URI / the resource's URI
    :return: 小寫的 scheme，沒有時為空字串 / the scheme in lower case, or an empty string
    """
    if not isinstance(uri, str) or _SCHEME_SEPARATOR not in uri:
        return ""
    return uri.split(_SCHEME_SEPARATOR, 1)[0].lower()


def uri_key(uri: str) -> str:
    """
    取得拿來比對與當作字典鍵的形式
    The form of a URI to compare and to key a dictionary with.

    同一個本機檔案可以有好幾種寫法（Windows 不分大小寫、斜線方向、``..``），直接
    拿字串比會把同一個檔案當成兩個。
    One local file can be spelled several ways (Windows ignores case, slashes go
    either way, ``..`` appears), and comparing the strings would treat it as two
    files.

    :param uri: 資源的 URI / the resource's URI
    :return: 正規化後的鍵 / the normalised key
    """
    path = to_path(uri)
    if not path:
        return uri
    return FILE_SCHEME_PREFIX + os.path.normcase(os.path.abspath(path))

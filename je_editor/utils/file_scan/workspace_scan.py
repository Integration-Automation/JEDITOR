"""
跨好幾個根目錄的檔案索引與 TODO 掃描
File indexing and TODO scanning across several roots.

單一根目錄的索引與掃描已經有了；這裡只是對每個根目錄各跑一次，並把結果的路徑變成
分得出根目錄的形式。只有一個根目錄時，顯示的路徑跟原本完全一樣。
Indexing and scanning one root already exist. This runs them once per root and
gives each result a path that tells the roots apart. With a single root, the
path shown is exactly what it always was.

純邏輯：不碰 Qt，因此可以在背景執行緒直接呼叫。
Pure logic: it touches no Qt, so a worker thread can call it directly.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from je_editor.utils.file_scan.file_indexer import DEFAULT_FILE_LIMIT, index_project_files
from je_editor.utils.file_scan.todo_scanner import (
    DEFAULT_TAGS, DEFAULT_TODO_LIMIT, TodoItem, scan_project_todos
)

# 一個根目錄：顯示名稱與路徑 / One root: its label and its path
LabelledRoot = tuple[str, str]


@dataclass(frozen=True)
class FoundFile:
    """
    索引到的一個檔案
    One file the index found.

    :param display_path: 給使用者看的路徑 / the path to show the user
    :param full_path: 用來開檔的完整路徑 / the full path to open it by
    """

    display_path: str
    full_path: str


@dataclass(frozen=True)
class FoundTodo:
    """
    掃描到的一筆待辦事項
    One TODO the scan found.

    :param item: 待辦事項，其中的路徑是給使用者看的 / the item, whose path is the one to show
    :param full_path: 用來開檔的完整路徑 / the full path to open it by
    """

    item: TodoItem
    full_path: str


def as_labelled_roots(roots: str | Path | Sequence[LabelledRoot]) -> list[LabelledRoot]:
    """
    接受單一路徑或一份根目錄清單，一律回傳清單
    Accept one path or a list of roots, and always give back a list.

    :param roots: 單一根目錄的路徑，或每個根目錄的顯示名稱與路徑
        the path of a single root, or each root's label and path
    :return: 每個根目錄的顯示名稱與路徑 / each root's label and path
    """
    if isinstance(roots, (str, Path)):
        return [(Path(roots).name or str(roots), str(roots))]
    return [(label, str(path)) for label, path in roots]


def shown_path(label: str, relative: str, several_roots: bool) -> str:
    """
    取得某個根目錄內的檔案要顯示的路徑
    The path to show for a file inside a root.

    :param label: 根目錄的顯示名稱 / the root's label
    :param relative: 根目錄內的相對路徑 / the path inside the root
    :param several_roots: 工作區是否有一個以上的根目錄 / whether the workspace has more than one root
    :return: 顯示用的路徑 / the path to show
    """
    return f"{label}/{relative}" if several_roots else relative


def index_workspace_files(
        roots: Sequence[LabelledRoot],
        limit: int = DEFAULT_FILE_LIMIT,
        should_stop: Callable[[], bool] | None = None) -> list[FoundFile]:
    """
    索引每個根目錄裡可編輯的檔案
    Index the editable files of every root.

    :param roots: 每個根目錄的顯示名稱與路徑 / each root's label and path
    :param limit: 回傳檔案數量上限，所有根目錄合計 / the cap on files returned, over all roots
    :param should_stop: 回傳 ``True`` 時提前中止 / returning ``True`` stops early
    :return: 找到的檔案，依根目錄順序 / the files found, in root order
    """
    several = len(roots) > 1
    found: list[FoundFile] = []
    for label, root in roots:
        if should_stop is not None and should_stop():
            break
        for relative in index_project_files(root, limit - len(found), should_stop):
            found.append(FoundFile(shown_path(label, relative, several), str(Path(root) / relative)))
        if len(found) >= limit:
            break
    return found


def scan_workspace_todos(
        roots: Sequence[LabelledRoot],
        tags: Sequence[str] = DEFAULT_TAGS,
        should_stop: Callable[[], bool] | None = None,
        limit: int = DEFAULT_TODO_LIMIT) -> list[FoundTodo]:
    """
    掃描每個根目錄裡的 TODO 註解
    Scan the TODO comments of every root.

    :param roots: 每個根目錄的顯示名稱與路徑 / each root's label and path
    :param tags: 要比對的標籤 / the tags to match
    :param should_stop: 回傳 ``True`` 時提前中止 / returning ``True`` stops early
    :param limit: 回傳數量上限，所有根目錄合計 / the cap on items returned, over all roots
    :return: 找到的項目，依根目錄順序 / the items found, in root order
    """
    several = len(roots) > 1
    found: list[FoundTodo] = []
    for label, root in roots:
        if should_stop is not None and should_stop():
            break
        for item in scan_project_todos(root, tags, should_stop, limit - len(found)):
            found.append(FoundTodo(
                replace(item, path=shown_path(label, item.path, several)),
                str(Path(root) / item.path)))
        if len(found) >= limit:
            break
    return found

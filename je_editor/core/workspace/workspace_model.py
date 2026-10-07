"""
工作區：零到多個專案根目錄
A workspace: zero or more project roots.

編輯器原本只認得「一個專案目錄」。工作區把它變成清單，但只有一個根目錄的工作區
仍然是完全合法的工作區，行為要跟原本一樣。
The editor used to know one project directory. A workspace turns that into a
list, while a workspace holding a single root stays perfectly valid and has to
behave as the editor always did.

純邏輯：不讀寫磁碟，也不碰 Qt。
Pure logic: it reads nothing from disk and touches no Qt.
"""
from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from je_editor.core.events.event_hook import EventHook
from je_editor.core.uri.resource_uri import (
    is_local_uri, to_path, to_uri, uri_key, uri_scheme
)
from je_editor.utils.exception.exceptions import JEditorServiceException


@dataclass(frozen=True)
class ProjectRoot:
    """
    工作區裡的一個根目錄
    One root inside a workspace.

    :param uri: 根目錄的 URI / the root's URI
    :param name: 顯示名稱 / the name to show
    """

    uri: str
    name: str

    @classmethod
    def from_path(cls, path: str | Path, name: str = "") -> ProjectRoot:
        """
        由本機目錄建立根目錄
        Build a root from a local directory.

        目錄不必已經存在：還原工作階段時，上次的目錄可能暫時不在。
        The directory need not exist: when a session is restored, last time's
        directory may be missing for now.

        :param path: 目錄路徑 / the directory
        :param name: 顯示名稱，沒給時用目錄名稱 / the name to show, the directory's
            own name when omitted
        :return: 根目錄 / the root
        """
        absolute = os.path.abspath(str(path))
        return cls(uri=to_uri(absolute), name=name or Path(absolute).name or absolute)

    @property
    def is_local(self) -> bool:
        """這個根目錄是否在本機 / Whether this root is on this machine."""
        return is_local_uri(self.uri)

    @property
    def path(self) -> str:
        """本機路徑；不在本機時為空字串 / The local path, empty when not local."""
        return to_path(self.uri)

    def contains(self, path: str | Path) -> bool:
        """
        判斷某個本機路徑是否在這個根目錄底下
        Whether a local path lies inside this root.

        :param path: 檔案或目錄路徑 / the file or directory
        :return: 在底下（或就是根目錄本身）時為 ``True`` / ``True`` when it is
            inside, or is the root itself
        """
        if not self.is_local:
            return False
        root_key = _path_key(self.path)
        candidate = _path_key(path)
        return candidate == root_key or candidate.startswith(root_key.rstrip(os.sep) + os.sep)

    def resolve(self, relative_path: str | Path) -> str:
        """
        把根目錄內的相對路徑轉成完整路徑
        Turn a path relative to this root into a full path.

        :param relative_path: 相對於根目錄的路徑 / the path relative to the root
        :return: 完整的本機路徑 / the full local path
        :raises JEditorServiceException: 根目錄不在本機，或結果跑到根目錄外面
            （例如 ``..``）/ when the root is not local, or the result escapes
            the root, as ``..`` can
        """
        if not self.is_local:
            raise JEditorServiceException(f"{self.uri} is not a local root")
        resolved = os.path.abspath(os.path.join(self.path, str(relative_path)))
        if not self.contains(resolved):
            raise JEditorServiceException(f"{relative_path} leaves the project root {self.path}")
        return resolved


def _path_key(path: str | Path) -> str:
    """比對路徑用的正規化形式 / The normalised form used to compare paths."""
    return os.path.normcase(os.path.abspath(str(path)))


class Workspace:
    """
    一個視窗正在處理的所有根目錄
    Every root one window is working on.
    """

    def __init__(self, roots: Iterable[ProjectRoot] = ()) -> None:
        """
        :param roots: 一開始就有的根目錄 / the roots to start with
        """
        self._roots: tuple[ProjectRoot, ...] = ()
        self._lock = Lock()
        # 根目錄增減之後發出，引數是這個工作區
        # Fired after a root is added or removed, with this workspace
        self.changed = EventHook("workspace changed")
        for root in roots:
            self._insert(root)

    @classmethod
    def single_root(cls, path: str | Path) -> Workspace:
        """
        建立只有一個根目錄的工作區，也就是原本的「專案目錄」
        A workspace with one root, which is what a project directory used to be.

        :param path: 專案目錄 / the project directory
        :return: 工作區 / the workspace
        """
        return cls([ProjectRoot.from_path(path)])

    @property
    def roots(self) -> tuple[ProjectRoot, ...]:
        """目前的根目錄，依加入順序 / The roots, in the order they were added."""
        return self._roots

    @property
    def primary_root(self) -> ProjectRoot | None:
        """第一個根目錄；沒有根目錄時為 ``None`` / The first root, or ``None``."""
        roots = self._roots
        return roots[0] if roots else None

    @property
    def is_multi_root(self) -> bool:
        """是否有一個以上的根目錄 / Whether there is more than one root."""
        return len(self._roots) > 1

    def add_root(self, root: ProjectRoot | str | Path) -> bool:
        """
        加入一個根目錄
        Add a root.

        :param root: 根目錄，或本機目錄路徑 / the root, or a local directory
        :return: 是否真的加入（已經有同一個根目錄時為 ``False``）
            whether it was added, ``False`` when that root is already present
        """
        added = self._insert(root if isinstance(root, ProjectRoot) else ProjectRoot.from_path(root))
        if added:
            self.changed.emit(self)
        return added

    def remove_root(self, root: ProjectRoot | str | Path) -> bool:
        """
        移除一個根目錄
        Remove a root.

        :param root: 根目錄、它的 URI，或本機目錄路徑 / the root, its URI, or a
            local directory
        :return: 是否真的移除了 / whether a root was removed
        """
        key = _root_key(root)
        with self._lock:
            kept = tuple(item for item in self._roots if uri_key(item.uri) != key)
            removed = len(kept) != len(self._roots)
            self._roots = kept
        if removed:
            self.changed.emit(self)
        return removed

    def root_for(self, path: str | Path) -> ProjectRoot | None:
        """
        找出某個本機路徑屬於哪個根目錄
        The root a local path belongs to.

        根目錄可以互相包含，這時取最深的那一個：``/a/b/x.py`` 屬於 ``/a/b`` 而
        不是 ``/a``。
        Roots may nest, in which case the deepest one wins: ``/a/b/x.py`` belongs
        to ``/a/b`` rather than ``/a``.

        :param path: 檔案或目錄路徑 / the file or directory
        :return: 所屬的根目錄，不屬於任何一個時為 ``None`` / the owning root, or ``None``
        """
        owners = [root for root in self._roots if root.contains(path)]
        if not owners:
            return None
        return max(owners, key=lambda root: len(_path_key(root.path)))

    def root_for_uri(self, uri: str) -> ProjectRoot | None:
        """
        找出某個資源屬於哪個根目錄
        The root a resource belongs to.

        文件與診斷都以 URI 指認，所以這是它們找根目錄的入口；本機與不在本機的根
        目錄都找得到。
        Documents and diagnostics are named by URI, so this is how they find
        their root, whether that root is on this machine or not.

        :param uri: 資源的 URI / the resource's URI
        :return: 所屬的根目錄，不屬於任何一個時為 ``None`` / the owning root, or ``None``
        """
        path = to_path(uri)
        if path:
            return self.root_for(path)
        owners = [
            root for root in self._roots
            if not root.is_local and _uri_inside(root.uri, uri)
        ]
        return max(owners, key=lambda root: len(root.uri)) if owners else None

    def relative_path(self, path: str | Path) -> tuple[ProjectRoot, str] | None:
        """
        把本機路徑拆成「根目錄」與「根目錄內的相對路徑」
        Split a local path into its root and the path inside that root.

        兩個根目錄底下可以有同名的檔案，所以相對路徑要跟根目錄一起才不會撞在一起。
        Two roots can each hold a file of the same name, so a relative path only
        identifies a file together with its root.

        :param path: 檔案或目錄路徑 / the file or directory
        :return: ``(根目錄, 相對路徑)``，不屬於任何根目錄時為 ``None``
            ``(root, relative path)``, or ``None`` outside every root
        """
        root = self.root_for(path)
        if root is None:
            return None
        relative = os.path.relpath(os.path.abspath(str(path)), root.path)
        return root, Path(relative).as_posix()

    def _insert(self, root: ProjectRoot) -> bool:
        """加入根目錄，重複的不加 / Add a root unless it is already there."""
        key = uri_key(root.uri)
        with self._lock:
            if any(uri_key(item.uri) == key for item in self._roots):
                return False
            self._roots = self._roots + (root,)
            return True


def _uri_inside(root_uri: str, uri: str) -> bool:
    """判斷 URI 是否在某個根目錄的 URI 底下 / Whether a URI lies beneath a root's URI."""
    return uri == root_uri or uri.startswith(root_uri.rstrip("/") + "/")


def _root_key(root: ProjectRoot | str | Path) -> str:
    """把各種指認根目錄的方式轉成同一種鍵 / One key for every way of naming a root."""
    if isinstance(root, ProjectRoot):
        return uri_key(root.uri)
    text = str(root)
    return uri_key(text if uri_scheme(text) else to_uri(text))

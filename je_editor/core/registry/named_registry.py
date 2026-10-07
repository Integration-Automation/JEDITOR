"""
以名稱保管可替換的實作
Keep interchangeable implementations by name.

AI 供應者、除錯轉接器、遠端傳輸與工作執行器都是「同一個介面、好幾個實作」，而且
都要讓外掛或宿主程式自己加。它們共用這一個登記表，而不是各寫一份。
AI providers, debug adapters, remote transports and task runners are each one
interface with several implementations, and each has to accept more from a
plugin or a host application. They share this one registry instead of having one
apiece.
"""
from __future__ import annotations

from threading import Lock
from typing import Generic, TypeVar

from je_editor.core.events.event_hook import EventHook
from je_editor.utils.exception.exceptions import JEditorServiceException

ItemT = TypeVar("ItemT")


class NamedRegistry(Generic[ItemT]):
    """
    名稱對應實作的登記表
    A registry from a name to an implementation.
    """

    def __init__(self, kind: str) -> None:
        """
        :param kind: 登記的是哪一種東西，用在錯誤訊息 / what is being registered,
            used in error messages
        """
        self._kind = kind
        self._items: dict[str, ItemT] = {}
        self._lock = Lock()
        # 登記或移除之後發出，引數是名稱 / Fired after a change, with the name
        self.changed = EventHook(f"{kind} registry changed")

    def register(self, name: str, item: ItemT, replace: bool = False) -> None:
        """
        登記一個實作
        Register an implementation.

        :param name: 名稱 / the name to register under
        :param item: 實作 / the implementation
        :param replace: 名稱已被使用時是否取代 / whether to replace an existing entry
        :raises JEditorServiceException: 名稱是空的，或已被使用而且沒有要求取代
            when the name is empty, or taken and *replace* is not set
        """
        if not isinstance(name, str) or not name.strip():
            raise JEditorServiceException(f"A {self._kind} needs a non-empty name")
        with self._lock:
            if name in self._items and not replace:
                raise JEditorServiceException(f"A {self._kind} named {name!r} is already registered")
            self._items[name] = item
        self.changed.emit(name)

    def unregister(self, name: str) -> ItemT | None:
        """
        移除一個實作
        Remove an implementation.

        :param name: 名稱 / the name it was registered under
        :return: 被移除的實作，沒有這個名稱時為 ``None`` / what was removed, or ``None``
        """
        with self._lock:
            item = self._items.pop(name, None)
        if item is not None:
            self.changed.emit(name)
        return item

    def get(self, name: str) -> ItemT | None:
        """
        取得某個名稱的實作
        The implementation registered under a name.

        :param name: 名稱 / the name
        :return: 實作，沒有時為 ``None`` / the implementation, or ``None``
        """
        with self._lock:
            return self._items.get(name)

    def require(self, name: str) -> ItemT:
        """
        取得某個名稱的實作，沒有就報錯
        The implementation registered under a name, which has to exist.

        :param name: 名稱 / the name
        :return: 實作 / the implementation
        :raises JEditorServiceException: 沒有這個名稱 / when nothing has that name
        """
        item = self.get(name)
        if item is None:
            known = ", ".join(self.names()) or "none"
            raise JEditorServiceException(
                f"No {self._kind} named {name!r} is registered (registered: {known})")
        return item

    def names(self) -> list[str]:
        """已登記的名稱，依登記順序 / The registered names, in registration order."""
        with self._lock:
            return list(self._items)

    def items(self) -> list[tuple[str, ItemT]]:
        """已登記的名稱與實作 / The registered names and implementations."""
        with self._lock:
            return list(self._items.items())

    def __contains__(self, name: object) -> bool:
        with self._lock:
            return name in self._items

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

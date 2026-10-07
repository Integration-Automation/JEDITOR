"""
不靠 Qt 的事件通知
Event notification that does not need Qt.

核心服務要能在沒有 ``QApplication`` 的地方使用，因此不能用 Qt 的訊號。這裡提供同樣
的「訂閱、通知」，Qt 這一層再把它接到自己的訊號上。
The core services have to work where there is no ``QApplication``, which rules
out Qt signals. This gives the same subscribe-and-notify shape, and the Qt layer
connects it to signals of its own.

訂閱者在發出通知的那個執行緒上被呼叫；要更新畫面的訂閱者得自己轉回 UI 執行緒。
A subscriber is called on whichever thread emits, so one that updates widgets
has to hand over to the UI thread itself.
"""
from __future__ import annotations

from collections.abc import Callable
from threading import Lock

from je_editor.utils.logging.loggin_instance import jeditor_logger

# 訂閱者的型別 / What a subscriber looks like
Listener = Callable[..., None]


class EventHook:
    """
    一個可訂閱的事件
    One event that can be subscribed to.
    """

    def __init__(self, name: str = "") -> None:
        """
        :param name: 事件名稱，只用在日誌 / the event's name, used only in the log
        """
        self._name = name
        self._listeners: list[Listener] = []
        self._lock = Lock()

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        """
        訂閱這個事件
        Subscribe to this event.

        :param listener: 事件發生時要呼叫的函式 / what to call when it fires
        :return: 取消這次訂閱的函式 / a function that undoes this subscription
        """
        with self._lock:
            self._listeners.append(listener)

        def unsubscribe() -> None:
            self.unsubscribe(listener)

        return unsubscribe

    def unsubscribe(self, listener: Listener) -> bool:
        """
        取消訂閱
        Stop a listener from being called.

        :param listener: 先前訂閱的函式 / the function subscribed earlier
        :return: 是否真的移除了訂閱 / whether a subscription was removed
        """
        with self._lock:
            if listener not in self._listeners:
                return False
            self._listeners.remove(listener)
            return True

    def emit(self, *args: object) -> None:
        """
        通知每一個訂閱者
        Call every subscriber.

        一個訂閱者出錯不會擋住其他訂閱者：問題面板的例外不該讓縮圖收不到同一筆
        通知。錯誤會寫進日誌。
        One failing subscriber does not stop the rest: an error in the problems
        panel must not keep the minimap from hearing the same news. The failure
        is logged.

        :param args: 交給訂閱者的引數 / what to pass to each subscriber
        """
        with self._lock:
            # 複製一份再呼叫，訂閱者才能在回呼裡取消訂閱
            # Call a copy, so a subscriber can unsubscribe from inside its callback
            listeners = tuple(self._listeners)
        for listener in listeners:
            try:
                listener(*args)
            # 訂閱者是別人的程式碼，會丟什麼例外無從列舉；這裡是隔離邊界，記錄後繼續
            # Subscribers are foreign code whose exceptions cannot be enumerated;
            # this is the isolation boundary, so log and carry on
            except Exception:  # noqa: BLE001
                jeditor_logger.exception("event %s: a subscriber failed", self._name or "<unnamed>")

    def __len__(self) -> int:
        """目前有幾個訂閱者 / How many subscribers there are."""
        with self._lock:
            return len(self._listeners)

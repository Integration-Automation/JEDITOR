"""
在背景執行緒向 AI 供應者發出請求
Ask an AI provider on a worker thread.

供應者的 ``complete()`` 會等到整個回覆回來，在 UI 執行緒呼叫會讓視窗整段時間沒有
反應。這裡把它搬到背景，回覆的每一段、最後的結果與錯誤都用訊號送回 UI 執行緒。
A provider's ``complete()`` waits for the whole reply, and calling it on the UI
thread would leave the window unresponsive for all of it. This moves the call to
a worker thread and hands each piece of the reply, the final result and any
error back to the UI thread as signals.

用的是 Python 的 daemon 執行緒而不是 ``QThread``：有些請求無法中途打斷，視窗關閉
時它可能還在等網路。執行中的 ``QThread`` 被銷毀會讓 Qt 中止整個程序，daemon 執行緒
則只是跟著程序一起結束。
A Python daemon thread is used rather than a ``QThread``: some requests cannot
be interrupted, and one may still be waiting on the network when the window
closes. Qt aborts the process if a running ``QThread`` is destroyed, whereas a
daemon thread simply ends with the process.
"""
from __future__ import annotations

from threading import Thread

from PySide6.QtCore import QObject, Signal

from je_editor.core.ai.ai_provider import AIProvider, CancelToken, ChatRequest
from je_editor.utils.exception.exceptions import JEditorServiceException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 等一個請求結束的預設時間（毫秒）/ How long to wait for one request by default, in milliseconds
DEFAULT_WAIT_MS = 5000
_MS_PER_SECOND = 1000
# 還在執行的工作。面板可能在回覆回來之前就關掉，訊號的發送端不能跟著它被刪除，
# 所以由這裡留住，跑完才放掉。
# The workers still running. A panel may close before the reply arrives and the
# object emitting the signals must not be deleted with it, so each one is kept
# here until it has finished.
_live_workers: set[ChatWorker] = set()


class ChatWorker(QObject):
    """
    送出一個對話請求
    Send one chat request.
    """

    text_ready = Signal(str)  # one piece of the reply, as it is generated
    replied = Signal(object)  # the finished ChatResponse
    failed = Signal(str)  # what went wrong, in words for the user
    finished = Signal()  # always last, whatever happened

    def __init__(self, provider: AIProvider, request: ChatRequest) -> None:
        """
        :param provider: 要詢問的供應者 / the provider to ask
        :param request: 對話請求 / the chat request
        """
        # 不設父物件：它的壽命由 _live_workers 管，不跟著面板
        # No parent: _live_workers decides how long it lives, not the panel
        super().__init__()
        self._provider = provider
        self._request = request
        self._cancel = CancelToken()
        self._thread = Thread(target=self._run, name="ChatWorker", daemon=True)
        self.finished.connect(self._release)

    def start_request(self) -> None:
        """開始執行，並在執行期間留住自己 / Start, and keep itself alive while it runs."""
        _live_workers.add(self)
        self._thread.start()

    def cancel(self) -> None:
        """要求取消；供應者會在下一段文字到達時停下來 / Ask for a cancel; the provider stops at the next piece."""
        self._cancel.cancel()

    def wait(self, timeout_ms: int = DEFAULT_WAIT_MS) -> bool:
        """
        等這個請求結束
        Wait for this request to finish.

        :param timeout_ms: 最多等多久（毫秒）/ how long to wait at most, in milliseconds
        :return: 是否已經結束 / whether it has finished
        """
        if self._thread.ident is not None:
            self._thread.join(timeout_ms / _MS_PER_SECOND)
        return not self._thread.is_alive()

    def _run(self) -> None:
        """呼叫供應者並回報結果 / Call the provider and report what came of it."""
        try:
            response = self._provider.complete(self._request, self.text_ready.emit, self._cancel)
        except JEditorServiceException as error:
            self.failed.emit(str(error))
        # 供應者可以來自外掛，會丟什麼例外無從列舉；這裡是執行緒的邊界，漏掉的例外
        # 會讓面板永遠停在「等待回覆」
        # A provider may come from a plugin and its exceptions cannot be
        # enumerated. This is the thread's boundary: an exception that escaped
        # would leave the panel waiting for a reply for ever
        except Exception as error:
            jeditor_logger.exception("ChatWorker: the provider raised an unexpected error")
            self.failed.emit(f"{type(error).__name__}: {error}")
        else:
            self.replied.emit(response)
        finally:
            self.finished.emit()

    def _release(self) -> None:
        """跑完了：放掉參考並刪除自己 / Finished: let go of the reference and delete itself."""
        _live_workers.discard(self)
        self.deleteLater()


def cancel_chat_workers() -> None:
    """
    取消所有還在執行的請求
    Cancel every request that is still running.
    """
    for worker in list(_live_workers):
        worker.cancel()


def wait_for_chat_workers(timeout_ms: int = DEFAULT_WAIT_MS) -> bool:
    """
    等所有還在執行的請求結束
    Wait for every request that is still running.

    :param timeout_ms: 每個請求最多等多久（毫秒）/ how long to wait for each one, in milliseconds
    :return: 是否全部都結束了 / whether all of them finished
    """
    return all(worker.wait(timeout_ms) for worker in list(_live_workers))

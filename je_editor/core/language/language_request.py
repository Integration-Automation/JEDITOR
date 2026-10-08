"""
向語言服務發問與收到回覆的形式
The shape of a question put to a language service, and of its reply.

語言伺服器要過一陣子才回答，語法解析器當場就能回答；呼叫的人不該需要知道是哪一種。
所以發問一律是「給一個收回覆的函式，拿回一個取消的函式」：當場能答的服務在
``request()`` 回傳之前就呼叫它，要等的服務之後再呼叫。
A language server answers after a while and a syntax parser answers on the spot,
and the caller should not have to know which it is talking to. So a question
always hands over a function to receive the reply and gets back a function to
cancel with: a service that can answer at once calls it before ``request()``
returns, and one that has to wait calls it later.

回覆最多只會送達一次，取消之後不會再送達。等待中的服務可能從自己的執行緒回覆，
要更新畫面的呼叫端得自己把它轉回畫面執行緒。
A reply arrives at most once and never after a cancel. A service that waits may
reply from a thread of its own, so a caller that updates widgets has to move the
reply back to the widget thread itself.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from je_editor.core.diagnostics.diagnostic_model import Position
from je_editor.core.document.document_model import Document
from je_editor.core.language.language_capability import LanguageCapability


@dataclass(frozen=True)
class LanguageRequest:
    """
    向語言服務問的一個問題
    One question put to a language service.

    :param capability: 問的是哪一種功能 / which capability is being asked for
    :param document: 問的是哪一份文件 / the document it is about
    :param position: 問的是文件裡的哪個位置；跟位置無關的問題不用給
        the position in the document, omitted for questions that have none
    :param options: 該功能自己的額外參數 / further parameters of that capability
    """

    capability: LanguageCapability
    document: Document
    position: Position | None = None
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class LanguageReply:
    """
    語言服務對一個問題的回覆
    A language service's reply to one question.

    ``value`` 的型別由功能決定：``SYNTAX_TREE`` 是那份文件的
    :class:`~je_editor.core.syntax.syntax_model.SyntaxSession`，``DOCUMENT_SYMBOLS``
    是有名稱的 :class:`~je_editor.core.syntax.syntax_model.StructuralRegion`。
    其餘功能的型別在第一個提供它的服務出現時決定。
    The type of ``value`` depends on the capability: for ``SYNTAX_TREE`` it is
    the document's :class:`~je_editor.core.syntax.syntax_model.SyntaxSession`,
    and for ``DOCUMENT_SYMBOLS`` the named
    :class:`~je_editor.core.syntax.syntax_model.StructuralRegion` objects. The
    other capabilities get theirs when the first service offers them.

    :param request: 這是哪個問題的回覆 / the question this answers
    :param service: 回答的服務名稱，沒有服務能回答時為空字串
        the name of the service that answered, empty when none could
    :param value: 答案 / the answer
    :param error: 答不出來的原因，答得出來時為空字串
        why there is no answer, empty when there is one
    """

    request: LanguageRequest
    service: str = ""
    value: object = None
    error: str = ""

    @property
    def ok(self) -> bool:
        """是否答出來了 / Whether there is an answer."""
        return not self.error


ReplyHandler = Callable[[LanguageReply], None]
CancelRequest = Callable[[], None]


def nothing_to_cancel() -> None:
    """已經答完的問題沒有東西可以取消 / A question already answered has nothing to cancel."""


class ReplyOnce:
    """
    保證回覆最多送達一次、取消之後不再送達
    Makes sure a reply arrives at most once, and never after a cancel.

    登記表把它包在呼叫端的函式外面，所以每個服務不必各自處理「回覆與取消同時發生」。
    The registry wraps the caller's function in this, so no service has to deal
    with a reply and a cancel happening at the same moment on its own.
    """

    def __init__(self, on_reply: ReplyHandler) -> None:
        """
        :param on_reply: 呼叫端收回覆的函式 / the caller's function for the reply
        """
        self._on_reply = on_reply
        self._lock = threading.Lock()
        self._settled = False
        self._cancel_service: CancelRequest = nothing_to_cancel

    @property
    def settled(self) -> bool:
        """是否已經回覆或取消 / Whether it has been answered or cancelled."""
        return self._settled

    def __call__(self, reply: LanguageReply) -> None:
        """
        送達回覆；已經回覆或取消過的話就丟掉
        Deliver the reply, or drop it when one was delivered or it was cancelled.

        :param reply: 服務的回覆 / the service's reply
        """
        if self._settle():
            self._on_reply(reply)

    def cancel(self) -> None:
        """
        取消這個問題，並請服務停止處理
        Cancel the question and ask the service to stop working on it.
        """
        if self._settle():
            self._cancel_service()

    def attach(self, cancel_service: CancelRequest) -> CancelRequest:
        """
        記下服務給的取消函式
        Remember the cancel function the service returned.

        :param cancel_service: 服務的取消函式 / the service's cancel function
        :return: 呼叫端用來取消的函式 / the function the caller cancels with
        """
        self._cancel_service = cancel_service
        return self.cancel

    def _settle(self) -> bool:
        """搶到「第一個」時回傳 ``True`` / ``True`` for whoever gets there first."""
        with self._lock:
            if self._settled:
                return False
            self._settled = True
            return True

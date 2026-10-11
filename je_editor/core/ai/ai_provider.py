"""
AI 供應者的介面
The interface for an AI provider.

對話面板只該知道「送出一段對話、拿回回覆」，不該知道背後是哪一家的模型或哪一個
SDK。每一家各自實作這個介面並登記，面板就不必為了新增一家而改。
The chat panel should know only how to send a conversation and get a reply,
never whose model or which SDK is behind it. Each vendor implements this
interface and registers itself, so adding one never changes the panel.

這裡只有介面與資料物件，不連線到任何服務。
This holds the interface and its data objects only, and connects to no service.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from threading import Event
from typing import Protocol, runtime_checkable


class ChatRole(Enum):
    """
    一則訊息是誰說的
    Who said a message.
    """

    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class ChatMessage:
    """
    對話裡的一則訊息
    One message of a conversation.

    :param role: 誰說的 / who said it
    :param content: 內容 / what was said
    """

    role: ChatRole
    content: str


@dataclass(frozen=True)
class ModelInfo:
    """
    供應者提供的一個模型
    One model a provider offers.

    :param model_id: 呼叫時使用的識別字 / the identifier used when calling it
    :param display_name: 給使用者看的名稱 / the name to show the user
    :param supports_streaming: 是否能邊產生邊回傳 / whether it can answer as it generates
    """

    model_id: str
    display_name: str = ""
    supports_streaming: bool = False


@dataclass(frozen=True)
class ChatRequest:
    """
    一次對話請求
    One chat request.

    :param messages: 到目前為止的對話，最後一則是這次要回答的
        the conversation so far, the last message being the one to answer
    :param model_id: 要用的模型，空字串表示供應者的預設
        the model to use, empty for the provider's default
    :param system_prompt: 系統提示詞 / the system prompt
    """

    messages: tuple[ChatMessage, ...]
    model_id: str = ""
    system_prompt: str = ""


@dataclass(frozen=True)
class ChatResponse:
    """
    一次對話的回覆
    The reply to a chat request.

    :param text: 回覆的全文 / the whole reply
    :param model_id: 實際回答的模型 / the model that answered
    :param input_tokens: 請求用掉的 token 數，供應者沒回報時為 ``None``
        the tokens the request used, ``None`` when the provider does not say
    :param output_tokens: 回覆用掉的 token 數，供應者沒回報時為 ``None``
        the tokens the reply used, ``None`` when the provider does not say
    :param cancelled: 是否在完成前被取消 / whether it was cancelled before it finished
    """

    text: str
    model_id: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    cancelled: bool = False


class CancelToken:
    """
    讓呼叫端取消一次進行中的請求
    Lets the caller cancel a request in flight.

    請求在背景執行緒進行，取消則來自 UI 執行緒，所以用執行緒安全的旗標。
    The request runs on a worker thread while the cancel comes from the UI
    thread, hence a thread-safe flag.
    """

    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        """要求取消 / Ask for the request to be cancelled."""
        self._event.set()

    @property
    def cancelled(self) -> bool:
        """是否已經要求取消 / Whether a cancel has been asked for."""
        return self._event.is_set()


# 收到一段剛產生的文字時呼叫 / Called with each piece of text as it is generated
TextListener = Callable[[str], None]


@runtime_checkable
class AIProvider(Protocol):
    """
    一家 AI 服務
    One AI service.
    """

    @property
    def name(self) -> str:
        """供應者名稱，在登記表裡不能重複 / The provider's name, unique in the registry."""

    def models(self) -> list[ModelInfo]:
        """
        這個供應者提供哪些模型
        The models this provider offers.

        :return: 模型清單 / the models
        """

    def complete(self, request: ChatRequest, on_text: TextListener | None = None,
                 cancel: CancelToken | None = None) -> ChatResponse:
        """
        送出對話並等待回覆
        Send a conversation and wait for the reply.

        這個呼叫會等到回覆完成，所以要在背景執行緒呼叫，不能在 UI 執行緒。
        This call blocks until the reply is complete, so it belongs on a worker
        thread and never on the UI thread.

        :param request: 對話請求 / the chat request
        :param on_text: 每產生一段文字就呼叫一次；``None`` 表示只要最後的結果
            called with each piece of text as it is generated, or ``None`` to
            get only the final result
        :param cancel: 用來中途取消的旗標 / the token that cancels it part-way
        :return: 回覆 / the reply
        :raises JEditorServiceException: 服務回報錯誤，或設定不完整
            when the service reports an error or the configuration is incomplete
        """

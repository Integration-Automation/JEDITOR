"""
OpenAI 相容服務的供應者
The provider for OpenAI-compatible services.

透過 LangChain 的 ``ChatOpenAI`` 呼叫，所以任何 OpenAI 相容的端點（包含自架的）都
能用，只要給它位址、金鑰與模型名稱。
It calls through LangChain's ``ChatOpenAI``, so any OpenAI-compatible endpoint,
self-hosted ones included, works once it has an address, a key and a model name.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from je_editor.core.ai.ai_provider import (
    CancelToken, ChatRequest, ChatResponse, ChatRole, ModelInfo, TextListener
)
from je_editor.core.ai.ai_settings import ProviderSettings
from je_editor.utils.exception.exceptions import JEditorServiceException

PROVIDER_NAME = "openai"
# 推理模型把思考過程放在這個標籤前面，答案在它後面
# A reasoning model puts its thinking before this tag and the answer after it
_END_OF_REASONING = "</think>"
# LangChain 用來標示訊息角色的名稱 / The names LangChain uses for message roles
_SYSTEM_ROLE = "system"
_ROLE_NAMES = {ChatRole.USER: "human", ChatRole.ASSISTANT: "ai"}

# 取得目前設定的函式 / A function returning the settings as they are now
SettingsSource = Callable[[], ProviderSettings]
# 由設定與模型名稱建立聊天模型的函式 / Builds a chat model from the settings and a model name
ChatFactory = Callable[[ProviderSettings, str], Any]


def answer_after_reasoning(text: str) -> str:
    """
    去掉推理模型附在答案前面的思考過程
    Drop the thinking a reasoning model puts in front of its answer.

    只認第一個結束標籤：答案本身也可能提到這個標籤。
    Only the first closing tag counts, since the answer itself may mention it.

    :param text: 模型的完整回覆 / the model's whole reply
    :return: 答案；沒有思考過程時就是原文 / the answer, or the text unchanged when
        it carries no thinking
    """
    _reasoning, tag, answer = text.partition(_END_OF_REASONING)
    return answer.strip() if tag else text


def _build_chat_model(settings: ProviderSettings, model: str) -> Any:
    """建立 ``ChatOpenAI``；用到時才匯入 SDK / Build a ``ChatOpenAI``, importing the SDK only now."""
    from langchain_openai import ChatOpenAI
    options: dict[str, Any] = {"model": model}
    if settings.base_url:
        options["base_url"] = settings.base_url
    if settings.api_key:
        options["api_key"] = settings.api_key
    return ChatOpenAI(**options)


class OpenAIProvider:
    """
    OpenAI 相容服務
    An OpenAI-compatible service.
    """

    name = PROVIDER_NAME

    def __init__(self, settings: SettingsSource, chat_factory: ChatFactory = _build_chat_model) -> None:
        """
        :param settings: 取得目前設定的函式；每次呼叫都重新讀，所以改設定不必重建供應者
            returns the settings as they are now; read on every call, so a change
            of settings needs no new provider
        :param chat_factory: 建立聊天模型的函式，測試時換成假的
            builds the chat model, replaced by a fake in tests
        """
        self._settings = settings
        self._chat_factory = chat_factory

    def models(self) -> list[ModelInfo]:
        """
        這個供應者提供哪些模型
        The models this provider offers.

        OpenAI 相容的端點各有各的模型，沒有固定清單，由使用者自己填。
        Every OpenAI-compatible endpoint has models of its own, so there is no
        fixed list and the user names the model.

        :return: 空清單 / an empty list
        """
        return []

    def complete(self, request: ChatRequest, on_text: TextListener | None = None,
                 cancel: CancelToken | None = None) -> ChatResponse:
        """
        送出對話並等待回覆
        Send a conversation and wait for the reply.

        回覆是整份一次回來的：思考過程要等看到結束標籤才知道從哪裡切，邊收邊顯示
        會把它也顯示出來。
        The reply arrives whole: where the thinking ends is only known once the
        closing tag has been seen, and showing text as it arrives would show the
        thinking too.

        :param request: 對話請求 / the chat request
        :param on_text: 收到答案時呼叫一次 / called once, with the answer
        :param cancel: 用來取消的旗標；回覆回來時若已取消就丟掉
            the token that cancels it; a reply that arrives after a cancel is dropped
        :return: 回覆 / the reply
        :raises JEditorServiceException: 沒有指定模型，或服務回報錯誤
            when no model is named or the service reports an error
        """
        settings = self._settings()
        model = request.model_id or settings.model
        if not model:
            raise JEditorServiceException("No model is set for the OpenAI-compatible provider")
        message = self._invoke(settings, model, request)
        if cancel is not None and cancel.cancelled:
            return ChatResponse("", model, cancelled=True)
        answer = answer_after_reasoning(message.text)
        if on_text is not None and answer:
            on_text(answer)
        usage = getattr(message, "usage_metadata", None) or {}
        return ChatResponse(answer, model, usage.get("input_tokens"), usage.get("output_tokens"))

    def _invoke(self, settings: ProviderSettings, model: str, request: ChatRequest) -> Any:
        """呼叫模型，把 SDK 的錯誤轉成編輯器的例外 / Call the model, turning SDK errors into the editor's."""
        from openai import OpenAIError
        try:
            return self._chat_factory(settings, model).invoke(_as_langchain_messages(request, settings))
        # ValueError 也涵蓋 pydantic 對設定的驗證錯誤 / ValueError covers pydantic's validation of the settings too
        except (OpenAIError, ValueError) as error:
            raise JEditorServiceException(f"The OpenAI-compatible service failed: {error}") from error


def _as_langchain_messages(request: ChatRequest, settings: ProviderSettings) -> list[tuple[str, str]]:
    """把對話轉成 LangChain 的（角色, 內容）清單 / The conversation as LangChain's (role, content) pairs."""
    messages: list[tuple[str, str]] = []
    system_prompt = request.system_prompt or settings.system_prompt
    if system_prompt:
        messages.append((_SYSTEM_ROLE, system_prompt))
    messages.extend((_ROLE_NAMES[message.role], message.content) for message in request.messages)
    return messages

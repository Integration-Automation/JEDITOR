"""
Anthropic 的供應者
The provider for Anthropic.

直接使用官方的 ``anthropic`` SDK，以串流方式取得回覆，所以答案可以邊產生邊顯示，
也可以中途取消。
It uses the official ``anthropic`` SDK directly and reads the reply as a stream,
so the answer can be shown as it is generated and cancelled part-way.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from je_editor.core.ai.ai_provider import (
    CancelToken, ChatRequest, ChatResponse, ModelInfo, TextListener
)
from je_editor.core.ai.ai_settings import ProviderSettings
from je_editor.utils.exception.exceptions import JEditorServiceException

PROVIDER_NAME = "anthropic"
# 沒有指定模型時使用的模型 / The model used when none is named
DEFAULT_MODEL = "claude-opus-5-5"
# 串流請求的輸出上限；串流不受 HTTP 逾時限制，給足空間才不會把答案切斷
# The output cap for a streamed request; a stream is not bound by the HTTP
# timeout, and a generous cap keeps an answer from being cut short
MAX_OUTPUT_TOKENS = 64000
# 列在模型選單裡的模型；使用者仍然可以自己填別的
# The models offered in the model list; the user may still name another
_OFFERED_MODELS = (
    ModelInfo(DEFAULT_MODEL, "Claude Opus 5.5", supports_streaming=True),
    ModelInfo("claude-sonnet-5-5", "Claude Sonnet 5.5", supports_streaming=True),
    ModelInfo("claude-haiku-4-5", "Claude Haiku 4.5", supports_streaming=True),
    ModelInfo("claude-fable-5-1", "Claude Fable 5.1", supports_streaming=True),
)
# 這些模型的安全分類器可能拒絕請求；伺服器端的 fallback 會在被拒絕時自動改用另一個
# 模型重跑同一個請求，而不是把拒絕丟回來
# The safety classifiers of these models may decline a request. The server-side
# fallback re-runs a declined request on another model by itself instead of
# handing the refusal back
_MODELS_WITH_FALLBACK = frozenset({
    "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5", "claude-fable-5-1"})
_FALLBACK_BETA = "server-side-fallback-2026-07-01"
_FALLBACK_MODE = "default"
_REFUSAL = "refusal"

# 取得目前設定的函式 / A function returning the settings as they are now
SettingsSource = Callable[[], ProviderSettings]
# 由設定建立 SDK 用戶端的函式 / Builds the SDK client from the settings
ClientFactory = Callable[[ProviderSettings], Any]


def _build_client(settings: ProviderSettings) -> Any:
    """
    建立 SDK 用戶端；用到時才匯入 SDK
    Build the SDK client, importing the SDK only now.

    沒有填金鑰時不傳金鑰，讓 SDK 自己從環境（``ANTHROPIC_API_KEY`` 或登入的設定檔）
    找認證。
    With no key in the settings none is passed, which lets the SDK find its
    credentials in the environment (``ANTHROPIC_API_KEY`` or a logged-in profile).
    """
    import anthropic
    options: dict[str, str] = {}
    if settings.api_key:
        options["api_key"] = settings.api_key
    if settings.base_url:
        options["base_url"] = settings.base_url
    return anthropic.Anthropic(**options)


class AnthropicProvider:
    """
    Anthropic 的 Messages API
    Anthropic's Messages API.
    """

    name = PROVIDER_NAME

    def __init__(self, settings: SettingsSource, client_factory: ClientFactory = _build_client) -> None:
        """
        :param settings: 取得目前設定的函式；每次呼叫都重新讀，所以改設定不必重建供應者
            returns the settings as they are now; read on every call, so a change
            of settings needs no new provider
        :param client_factory: 建立 SDK 用戶端的函式，測試時換成假的
            builds the SDK client, replaced by a fake in tests
        """
        self._settings = settings
        self._client_factory = client_factory

    def models(self) -> list[ModelInfo]:
        """
        這個供應者提供哪些模型
        The models this provider offers.

        :return: 模型清單，第一個是預設 / the models, the default one first
        """
        return list(_OFFERED_MODELS)

    def complete(self, request: ChatRequest, on_text: TextListener | None = None,
                 cancel: CancelToken | None = None) -> ChatResponse:
        """
        送出對話並等待回覆
        Send a conversation and wait for the reply.

        :param request: 對話請求 / the chat request
        :param on_text: 每產生一段文字就呼叫一次 / called with each piece of text
            as it is generated
        :param cancel: 用來中途取消的旗標 / the token that cancels it part-way
        :return: 回覆；被取消時是已經收到的部分 / the reply, or what had arrived
            when it was cancelled
        :raises JEditorServiceException: 找不到認證、服務回報錯誤，或模型拒絕回答
            when no credentials are found, the service reports an error, or the
            model declines to answer
        """
        import anthropic
        settings = self._settings()
        model = request.model_id or settings.model or DEFAULT_MODEL
        try:
            return self._stream(self._client_factory(settings), settings, model, request,
                                on_text, cancel)
        except anthropic.APIError as error:
            raise JEditorServiceException(_describe(error)) from error
        # SDK 找不到任何認證時丟的是 TypeError / The SDK raises TypeError when it finds no credentials
        except TypeError as error:
            raise JEditorServiceException(
                "No Anthropic credentials were found. Set an API key in the AI settings or the "
                f"ANTHROPIC_API_KEY environment variable. ({error})") from error

    def _stream(self, client: Any, settings: ProviderSettings, model: str, request: ChatRequest,
                on_text: TextListener | None, cancel: CancelToken | None) -> ChatResponse:
        """開啟串流、逐段交出文字，最後整理成回覆 / Open the stream, hand text on piece by piece, sum up."""
        open_stream, parameters = _stream_call(client, settings, model, request)
        pieces: list[str] = []
        with open_stream(**parameters) as stream:
            for text in stream.text_stream:
                # 取消時直接離開；離開 with 區塊就會關掉連線
                # On a cancel, just leave: leaving the with block closes the connection
                if cancel is not None and cancel.cancelled:
                    return ChatResponse("".join(pieces), model, cancelled=True)
                pieces.append(text)
                if on_text is not None:
                    on_text(text)
            message = stream.get_final_message()
        if message.stop_reason == _REFUSAL:
            # 已經收到的片段不是完整的答案，不能當成回覆
            # What arrived so far is not a whole answer and must not pass for one
            category = getattr(message.stop_details, "category", None) or "unspecified"
            raise JEditorServiceException(
                f"The model declined to answer this request (category: {category})")
        return ChatResponse(
            "".join(pieces), message.model, message.usage.input_tokens, message.usage.output_tokens)


def _stream_call(client: Any, settings: ProviderSettings, model: str,
                 request: ChatRequest) -> tuple[Callable[..., Any], dict[str, Any]]:
    """
    決定要呼叫哪一個串流方法，以及它的參數
    Decide which stream method to call, and with what.

    fallback 是 beta 功能，只在直接連 Anthropic 的 API 時可用；設定了別的位址（代理、
    其他平台）時不送，否則整個請求會被拒絕。
    The fallback is a beta feature and only exists on Anthropic's own API. With
    another address set, a proxy or another platform, it is left out, since
    sending it would get the whole request rejected.
    """
    parameters: dict[str, Any] = {
        "model": model,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [{"role": message.role.value, "content": message.content}
                     for message in request.messages],
    }
    system_prompt = request.system_prompt or settings.system_prompt
    if system_prompt:
        parameters["system"] = system_prompt
    if model in _MODELS_WITH_FALLBACK and not settings.base_url:
        parameters["betas"] = [_FALLBACK_BETA]
        parameters["fallbacks"] = _FALLBACK_MODE
        return client.beta.messages.stream, parameters
    return client.messages.stream, parameters


def _describe(error: Exception) -> str:
    """
    把 SDK 的錯誤說成使用者看得懂的一句話，最具體的類別先判斷
    Put an SDK error into a sentence the user can act on, most specific class first.
    """
    import anthropic
    explanations: tuple[tuple[type, str], ...] = (
        (anthropic.AuthenticationError, "Anthropic rejected the API key"),
        (anthropic.PermissionDeniedError, "This API key may not use that model or feature"),
        (anthropic.NotFoundError, "Anthropic does not know that model"),
        (anthropic.RateLimitError, "Anthropic is rate limiting this key; try again shortly"),
        (anthropic.BadRequestError, "Anthropic rejected the request"),
        (anthropic.APIStatusError, "Anthropic returned an error"),
        (anthropic.APIConnectionError, "Could not reach Anthropic; check the network"),
    )
    for error_type, explanation in explanations:
        if isinstance(error, error_type):
            return f"{explanation}: {error}"
    return f"The Anthropic request failed: {error}"

"""
一段對話：記住說過的話，組出下一個請求
One conversation: it remembers what was said and builds the next request.

模型的 API 沒有狀態，每次都要把整段對話送過去。這裡保管那段對話，所以對話面板
只需要說「使用者問了這句」與「模型答了這句」。
A model's API keeps no state, so the whole conversation is sent every time. This
holds that conversation, leaving the chat panel to say only "the user asked
this" and "the model answered that".

純邏輯：不連線到任何服務，也不碰 Qt。
Pure logic: it connects to no service and touches no Qt.
"""
from __future__ import annotations

from je_editor.core.ai.ai_provider import ChatMessage, ChatRequest, ChatResponse, ChatRole


class ChatSession:
    """
    一段進行中的對話
    A conversation in progress.
    """

    def __init__(self) -> None:
        self._messages: list[ChatMessage] = []
        # 已經送出、還在等回覆的那一句 / The prompt that was sent and still awaits its reply
        self._pending: ChatMessage | None = None

    @property
    def messages(self) -> tuple[ChatMessage, ...]:
        """到目前為止完成的對話，不含還在等回覆的那一句 / The finished exchange, without a pending prompt."""
        return tuple(self._messages)

    @property
    def is_waiting(self) -> bool:
        """是否有一句話還在等回覆 / Whether a prompt is still waiting for its reply."""
        return self._pending is not None

    def ask(self, prompt: str, model_id: str = "", system_prompt: str = "") -> ChatRequest | None:
        """
        記下使用者的一句話，並組出要送給供應者的請求
        Note what the user said and build the request for the provider.

        這句話要等回覆回來才算進對話：失敗或取消時它不該留下來，否則下一次請求會
        帶著一句沒人回答過的話。
        The prompt only joins the conversation once its reply arrives. After a
        failure or a cancel it must not stay, or the next request would carry a
        question nobody answered.

        :param prompt: 使用者輸入的文字 / what the user typed
        :param model_id: 要用的模型 / the model to use
        :param system_prompt: 系統提示詞 / the system prompt
        :return: 請求；文字是空的，或上一句還在等回覆時為 ``None``
            the request, or ``None`` when the text is empty or a prompt is still waiting
        """
        text = prompt.strip()
        if not text or self.is_waiting:
            return None
        self._pending = ChatMessage(ChatRole.USER, text)
        return ChatRequest((*self._messages, self._pending), model_id, system_prompt)

    def answered(self, response: ChatResponse) -> bool:
        """
        記下模型的回覆
        Note the model's reply.

        被取消或是空的回覆不算進對話，連同那一句問話一起丟掉。
        A cancelled or empty reply does not join the conversation, and the
        prompt it answered is dropped with it.

        :param response: 供應者給的回覆 / the reply the provider gave
        :return: 這一問一答是否算進了對話 / whether the exchange joined the conversation
        """
        pending, self._pending = self._pending, None
        if pending is None or response.cancelled or not response.text:
            return False
        self._messages.extend((pending, ChatMessage(ChatRole.ASSISTANT, response.text)))
        return True

    def failed(self) -> None:
        """
        請求失敗了：丟掉還在等回覆的那一句
        The request failed: drop the prompt that was waiting.
        """
        self._pending = None

    def clear(self) -> None:
        """
        開始一段新的對話
        Start a new conversation.
        """
        self._messages = []
        self._pending = None

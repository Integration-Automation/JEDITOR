"""
把語法引擎接成語言服務
The syntax engine, offered as a language service.

登記之後，文件一開就有語法樹、文字一變就更新，其他服務或宿主程式可以用同一套
「發問、收回覆」取得某份文件的語法分析或它的符號，不必自己再解析一次。
Once registered, a document has a tree as soon as it opens and the tree follows
every change, and another service or a host application can ask for a document's
syntax analysis or its symbols through the ordinary request and reply, without
parsing it a second time.
"""
from __future__ import annotations

from je_editor.core.document.document_model import Document
from je_editor.core.language.language_capability import LanguageCapability
from je_editor.core.language.language_request import (
    CancelRequest, LanguageReply, LanguageRequest, ReplyHandler, nothing_to_cancel
)
from je_editor.core.syntax.syntax_model import SyntaxEngine, SyntaxSession
from je_editor.core.uri.resource_uri import uri_key

SERVICE_NAME = "syntax"


class SyntaxLanguageService:
    """
    提供語法樹與文件符號的語言服務
    The language service that offers the syntax tree and the document's symbols.
    """

    def __init__(self, engine: SyntaxEngine) -> None:
        """
        :param engine: 實際做分析的語法引擎 / the syntax engine that does the analysing
        """
        self._engine = engine
        self._sessions: dict[str, SyntaxSession] = {}

    @property
    def name(self) -> str:
        """服務名稱 / The service's name."""
        return SERVICE_NAME

    def capabilities(self) -> frozenset[LanguageCapability]:
        """
        這個服務提供哪些功能
        What this service offers.

        :return: 語法樹與文件符號 / the syntax tree and document symbols
        """
        return frozenset({LanguageCapability.SYNTAX_TREE, LanguageCapability.DOCUMENT_SYMBOLS})

    def handles(self, document: Document) -> bool:
        """
        引擎是否會分析這份文件的語言
        Whether the engine can analyse the document's language.

        :param document: 要判斷的文件 / the document in question
        :return: 會分析時為 ``True`` / ``True`` when it can
        """
        return self._language_of(document) is not None

    def document_opened(self, document: Document) -> None:
        """
        為開啟的文件建立語法樹
        Build the tree of a document that opened.

        :param document: 開啟的文件 / the document that opened
        """
        language_id = self._language_of(document)
        session = None if language_id is None else self._engine.open_session(language_id)
        if session is None:
            return
        session.update(document.text())
        self._sessions[uri_key(document.uri)] = session

    def document_changed(self, document: Document) -> None:
        """
        讓語法樹跟上文件的新內容
        Bring the tree up to date with a document's new text.

        :param document: 內容變了的文件 / the document that changed
        """
        session = self._sessions.get(uri_key(document.uri))
        if session is None:
            self.document_opened(document)
            return
        session.update(document.text())

    def document_closed(self, document: Document) -> None:
        """
        放掉關閉的文件的語法樹
        Let go of the tree of a document that closed.

        :param document: 關閉的文件 / the document that closed
        """
        self._sessions.pop(uri_key(document.uri), None)

    def session_for(self, document: Document) -> SyntaxSession | None:
        """
        取得一份開著的文件的語法分析
        The syntax analysis of a document that is open.

        :param document: 文件 / the document
        :return: 它的 session，文件沒開或語言不支援時為 ``None``
            its session, or ``None`` when it is not open or its language is not supported
        """
        return self._sessions.get(uri_key(document.uri))

    def request(self, request: LanguageRequest, on_reply: ReplyHandler) -> CancelRequest:
        """
        回答語法樹或文件符號的問題；答案是現成的，所以當場回覆
        Answer a question about the syntax tree or the document's symbols. The
        answer is at hand, so the reply comes at once.

        :param request: 問題 / the question
        :param on_reply: 收回覆的函式 / receives the reply
        :return: 沒有東西可以取消的取消函式 / a cancel function with nothing to cancel
        """
        session = self.session_for(request.document)
        if session is None:
            on_reply(LanguageReply(request, self.name,
                                   error=f"{request.document.uri} is not open in the syntax service"))
        elif request.capability is LanguageCapability.SYNTAX_TREE:
            on_reply(LanguageReply(request, self.name, value=session))
        elif request.capability is LanguageCapability.DOCUMENT_SYMBOLS:
            symbols = tuple(region for region in session.regions() if region.name)
            on_reply(LanguageReply(request, self.name, value=symbols))
        else:
            on_reply(LanguageReply(
                request, self.name,
                error=f"the syntax service does not offer {request.capability.value}"))
        return nothing_to_cancel

    def shutdown(self) -> None:
        """放掉每一棵語法樹 / Let go of every tree."""
        self._sessions.clear()

    def _language_of(self, document: Document) -> str | None:
        """文件的語言：先看它自己說的，再看檔名 / A document's language: what it says first, then its name."""
        if document.language_id and document.language_id in self._engine.language_ids():
            return document.language_id
        return self._engine.language_for(document.uri)

"""
語言服務的介面與登記表
The interface for language services, and the registry that holds them.

語言伺服器、之後的 Tree-sitter 解析器，或任何「看得懂某種語言」的東西，對編輯器
來說都是同一件事：告訴它文件開了、改了、關了，它就提供自己會的功能。登記表負責
把文件的生命週期轉給每一個處理該語言的服務。
A language server, the Tree-sitter parser to come, or anything else that
understands a language is one and the same thing to the editor: tell it a
document opened, changed or closed, and it offers what it can do. The registry
passes each document's lifecycle on to every service that handles its language.

補全、懸停說明這類「發問、等回覆」的呼叫形式由 Tree-sitter 與診斷那個里程碑決定，
這裡先固定生命週期與能力查詢。
The request-and-reply calls, completion and hover among them, take their shape
in the Tree-sitter and diagnostics milestone; this fixes the lifecycle and the
capability lookup first.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol, runtime_checkable

from je_editor.core.document.document_model import Document, DocumentStore
from je_editor.core.registry.named_registry import NamedRegistry


class LanguageCapability(Enum):
    """
    語言服務可以提供的功能
    What a language service can offer.
    """

    DIAGNOSTICS = "diagnostics"
    COMPLETION = "completion"
    HOVER = "hover"
    SIGNATURE_HELP = "signature_help"
    DEFINITION = "definition"
    REFERENCES = "references"
    RENAME = "rename"
    FORMATTING = "formatting"
    CODE_ACTION = "code_action"
    DOCUMENT_SYMBOLS = "document_symbols"
    SYNTAX_TREE = "syntax_tree"


@runtime_checkable
class LanguageService(Protocol):
    """
    一個看得懂某些語言的服務
    A service that understands some languages.
    """

    @property
    def name(self) -> str:
        """服務名稱，在登記表裡不能重複 / The service's name, unique in the registry."""

    def capabilities(self) -> frozenset[LanguageCapability]:
        """
        這個服務提供哪些功能
        What this service offers.

        :return: 功能的集合 / the set of capabilities
        """

    def handles(self, document: Document) -> bool:
        """
        這個服務是否處理某份文件
        Whether this service handles a document.

        :param document: 要判斷的文件 / the document in question
        :return: 會處理時為 ``True`` / ``True`` when it does
        """

    def document_opened(self, document: Document) -> None:
        """
        有一份它處理的文件開了
        A document it handles was opened.

        :param document: 開啟的文件 / the document that opened
        """

    def document_changed(self, document: Document) -> None:
        """
        有一份它處理的文件內容變了
        A document it handles changed.

        :param document: 內容變了的文件 / the document that changed
        """

    def document_closed(self, document: Document) -> None:
        """
        有一份它處理的文件關了
        A document it handles was closed.

        :param document: 關閉的文件 / the document that closed
        """

    def shutdown(self) -> None:
        """
        放掉這個服務持有的程序、執行緒與連線
        Release the processes, threads and connections this service holds.
        """


class LanguageServiceRegistry:
    """
    已登記的語言服務
    The language services that are registered.
    """

    def __init__(self, documents: DocumentStore) -> None:
        """
        :param documents: 文件的來源；它的開啟、變更與關閉會轉給各個服務
            where documents come from; its opens, changes and closes are passed
            on to the services
        """
        self._documents = documents
        self._services: NamedRegistry[LanguageService] = NamedRegistry("language service")
        self._unsubscribe: list[Callable[[], None]] = [
            documents.opened.subscribe(self._on_opened),
            documents.changed.subscribe(self._on_changed),
            documents.closed.subscribe(self._on_closed),
        ]

    def register(self, service: LanguageService) -> None:
        """
        登記一個語言服務
        Register a language service.

        已經開著的文件會補送一次「開啟」，晚啟動的伺服器才知道有哪些文件。
        Documents that are already open are announced to it, so a server that
        starts late still learns what is open.

        :param service: 要登記的服務 / the service
        :raises JEditorServiceException: 名稱是空的或已被使用 / when its name is
            empty or already taken
        """
        self._services.register(service.name, service)
        for document in self._documents.documents():
            if service.handles(document):
                service.document_opened(document)

    def unregister(self, name: str) -> bool:
        """
        移除並關閉一個語言服務
        Remove a language service and shut it down.

        :param name: 服務名稱 / the service's name
        :return: 是否真的移除了 / whether a service was removed
        """
        service = self._services.unregister(name)
        if service is None:
            return False
        service.shutdown()
        return True

    def services(self) -> list[LanguageService]:
        """已登記的服務，依登記順序 / The registered services, in registration order."""
        return [service for _name, service in self._services.items()]

    def services_for(self, document: Document,
                     capability: LanguageCapability | None = None) -> list[LanguageService]:
        """
        找出處理某份文件的服務
        The services that handle a document.

        :param document: 文件 / the document
        :param capability: 只要提供這個功能的服務，``None`` 表示不限
            only services offering this, or any service when ``None``
        :return: 符合的服務，依登記順序 / the matching services, in registration order
        """
        return [
            service for service in self.services()
            if service.handles(document)
            and (capability is None or capability in service.capabilities())
        ]

    def shutdown(self) -> None:
        """
        關閉每一個服務，並停止轉送文件事件
        Shut every service down and stop passing document events on.
        """
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._unsubscribe = []
        for name in self._services.names():
            self.unregister(name)

    def _on_opened(self, document: Document) -> None:
        """把「開啟」轉給處理它的服務 / Pass an open on to the services handling it."""
        for service in self.services_for(document):
            service.document_opened(document)

    def _on_changed(self, document: Document) -> None:
        """把「變更」轉給處理它的服務 / Pass a change on to the services handling it."""
        for service in self.services_for(document):
            service.document_changed(document)

    def _on_closed(self, document: Document) -> None:
        """把「關閉」轉給處理它的服務 / Pass a close on to the services handling it."""
        for service in self.services_for(document):
            service.document_closed(document)

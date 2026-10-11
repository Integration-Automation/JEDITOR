"""
文件模型：服務眼中的「一份開著的文件」
The document model: what an open document looks like to a service.

語言服務、診斷與除錯都只需要知道文件的 URI、語言、版本與內容，不需要知道它是
哪一種 Qt 元件。編輯器的緩衝區之後以轉接器的方式符合 :class:`Document`，這些服務
就不必認得編輯器。
Language services, diagnostics and debugging only need a document's URI,
language, version and text, never which Qt widget holds it. The editor's buffer
will satisfy :class:`Document` through an adapter, so those services never have
to know the editor.

純邏輯：不讀寫磁碟，也不碰 Qt。
Pure logic: it reads nothing from disk and touches no Qt.
"""
from __future__ import annotations

from threading import Lock
from typing import Protocol, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.core.uri.resource_uri import uri_key

# 文件剛開啟時的版本 / The version a document has when it is first opened
INITIAL_VERSION = 1


@runtime_checkable
class Document(Protocol):
    """
    服務需要知道的文件資訊
    What a service needs to know about a document.

    用 ``Protocol`` 而不是基底類別：之後由 ``QObject`` 持有緩衝區的轉接器可以直接
    符合，不必同時繼承兩種中繼類別。
    A ``Protocol`` rather than a base class, so an adapter whose buffer lives in
    a ``QObject`` can satisfy it without inheriting from two metaclasses.
    """

    @property
    def uri(self) -> str:
        """文件的 URI / The document's URI."""

    @property
    def language_id(self) -> str:
        """LSP 的 language id，例如 ``python`` / The LSP language id, such as ``python``."""

    @property
    def version(self) -> int:
        """內容每改一次就加一 / Goes up by one each time the text changes."""

    def text(self) -> str:
        """
        取得目前的全文
        The whole current text.

        :return: 文件內容 / the document's text
        """


class TextDocument:
    """
    內容放在記憶體裡的文件
    A document whose text is held in memory.

    用在沒有編輯器元件的地方：測試、命令列工具，或宿主程式自己管理的緩衝區。
    For places with no editor widget: tests, command-line tools, or a buffer the
    host application manages itself.
    """

    def __init__(self, uri: str, text: str = "", language_id: str = "") -> None:
        """
        :param uri: 文件的 URI / the document's URI
        :param text: 一開始的內容 / the text to start with
        :param language_id: LSP 的 language id / the LSP language id
        """
        self._uri = uri
        self._text = text
        self._language_id = language_id
        self._version = INITIAL_VERSION

    @property
    def uri(self) -> str:
        """文件的 URI / The document's URI."""
        return self._uri

    @property
    def language_id(self) -> str:
        """LSP 的 language id / The LSP language id."""
        return self._language_id

    @property
    def version(self) -> int:
        """內容每改一次就加一 / Goes up by one each time the text changes."""
        return self._version

    def text(self) -> str:
        """
        取得目前的全文
        The whole current text.

        :return: 文件內容 / the document's text
        """
        return self._text

    def set_text(self, text: str) -> bool:
        """
        換掉全文
        Replace the whole text.

        :param text: 新的內容 / the new text
        :return: 內容是否真的變了（沒變就不加版本）/ whether the text changed; the
            version only goes up when it did
        """
        if text == self._text:
            return False
        self._text = text
        self._version += 1
        return True


class DocumentStore:
    """
    目前開著的文件
    The documents that are currently open.

    以 URI 為鍵，所以同一個檔案不會被開成兩份。
    Keyed by URI, so one file is never opened as two documents.
    """

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}
        self._lock = Lock()
        # 三個事件的引數都是那份文件 / Each event passes the document concerned
        self.opened = EventHook("document opened")
        self.changed = EventHook("document changed")
        self.closed = EventHook("document closed")

    def open(self, document: Document) -> bool:
        """
        登記一份開著的文件
        Record a document as open.

        :param document: 要登記的文件 / the document
        :return: 是否真的登記了（同一個 URI 已經開著時為 ``False``）
            whether it was recorded, ``False`` when that URI is already open
        """
        key = uri_key(document.uri)
        with self._lock:
            if key in self._documents:
                return False
            self._documents[key] = document
        self.opened.emit(document)
        return True

    def close(self, uri: str) -> bool:
        """
        放掉一份文件
        Let go of a document.

        :param uri: 文件的 URI / the document's URI
        :return: 是否真的放掉了什麼 / whether a document was let go
        """
        with self._lock:
            document = self._documents.pop(uri_key(uri), None)
        if document is None:
            return False
        self.closed.emit(document)
        return True

    def get(self, uri: str) -> Document | None:
        """
        取得某個 URI 的文件
        The open document with a URI.

        :param uri: 文件的 URI / the document's URI
        :return: 文件，沒開著時為 ``None`` / the document, or ``None``
        """
        with self._lock:
            return self._documents.get(uri_key(uri))

    def documents(self) -> list[Document]:
        """目前開著的文件，依開啟順序 / The open documents, in the order they were opened."""
        with self._lock:
            return list(self._documents.values())

    def replace_text(self, uri: str, text: str) -> bool:
        """
        換掉一份記憶體文件的全文，並通知訂閱者
        Replace the text of an in-memory document and tell the subscribers.

        :param uri: 文件的 URI / the document's URI
        :param text: 新的內容 / the new text
        :return: 內容是否真的變了；文件沒開著，或不是 :class:`TextDocument` 時為
            ``False`` / whether the text changed; ``False`` when the document is
            not open or is not a :class:`TextDocument`
        """
        document = self.get(uri)
        if not isinstance(document, TextDocument) or not document.set_text(text):
            return False
        self.changed.emit(document)
        return True

    def notify_changed(self, uri: str) -> bool:
        """
        告訴訂閱者某份文件的內容變了
        Tell the subscribers a document's text changed.

        給緩衝區不在這裡的文件用：編輯器自己改了內容之後呼叫這個。
        For a document whose buffer lives elsewhere: the editor calls this after
        changing the text itself.

        :param uri: 文件的 URI / the document's URI
        :return: 文件是否開著 / whether the document is open
        """
        document = self.get(uri)
        if document is None:
            return False
        self.changed.emit(document)
        return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._documents)

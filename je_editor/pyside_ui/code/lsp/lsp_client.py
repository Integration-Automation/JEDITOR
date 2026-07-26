"""
一個檔案這一端的語言伺服器連線
One file's end of a language server connection.

伺服器程序本身由 ``lsp_session`` 保管並共用；這裡負責的是「這個檔案」的部分：
版本號、送出的請求、以及把回覆變成編輯器聽得懂的訊號。
The process itself is held and shared by ``lsp_session``; what lives here is the
part belonging to one file — its version number, the requests it sent, and
turning replies into signals the editor understands.

伺服器沒安裝、啟動失敗或中途結束時都只是「沒有補全」，不會影響編輯。
A server that is missing, fails to start, or dies mid-session simply means no
completions; editing carries on.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from je_editor.pyside_ui.code.lsp.lsp_session import LspSession, session_registry
from je_editor.utils.lsp.language_servers import language_id, server_command
from je_editor.utils.lsp.lsp_protocol import (
    completion_labels,
    definition_location,
    diagnostic_entries,
    file_uri,
    hover_text,
    notification,
    request,
    text_edits,
)


class LspClient(QObject):
    """
    一個檔案對應的語言伺服器連線
    One language server connection, for one file.
    """

    completions_ready = Signal(list)  # list[str]
    diagnostics_ready = Signal(list)  # list[dict]
    definition_ready = Signal(dict)  # {"path": str, "line": int, "column": int}
    hover_ready = Signal(str)
    edits_ready = Signal(list)  # list[dict] of text edits to apply

    def __init__(self, parent: QObject | None = None) -> None:
        """
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._session: LspSession | None = None
        self._file_path: str | None = None
        self._version = 0
        self._pending_completion_id: int | None = None
        self._pending_definition_id: int | None = None
        self._pending_hover_id: int | None = None
        self._pending_edit_id: int | None = None

    @property
    def running(self) -> bool:
        """伺服器是否正在執行 / Whether the server is running."""
        return self._session is not None and self._session.running

    def start_for(self, file_path: str, servers: dict | None = None) -> bool:
        """
        接上負責這個檔案的語言伺服器
        Attach to the language server that handles a file.

        同一個指令與專案根目錄底下的檔案共用一個伺服器程序，因此開第二個同語言的
        檔案不會再啟動一個。
        Files under the same command and project root share one process, so
        opening a second file of that language does not start another.

        :param file_path: 檔案路徑 / the file to serve
        :param servers: 伺服器對照表 / the server mapping to consult
        :return: 有接上時為 ``True`` / ``True`` when a server was attached
        """
        command = server_command(Path(file_path).suffix, servers)
        if command is None:
            return False
        self.stop()
        root = str(Path(file_path).parent)
        session = session_registry.session_for(command, root, file_uri(root))
        if session is None:
            return False
        self._session = session
        self._file_path = file_path
        session.register_document(file_uri(file_path), self)
        return True

    def _send(self, payload: dict) -> bool:
        """把訊息寫給伺服器 / Write a message to the server."""
        return self._session.send(payload) if self._session is not None else False

    def _send_request(self, payload: dict) -> bool:
        """送出請求，回覆會回到這個客戶端 / Send a request, so its reply comes back here."""
        return self._session.send_request(self, payload) if self._session is not None else False

    def _take_id(self) -> int:
        """取得下一個請求編號 / Take the next request id."""
        return self._session.take_id() if self._session is not None else 0

    def did_open(self, text: str) -> bool:
        """
        通知伺服器檔案已開啟
        Tell the server the file is open.

        :param text: 目前內容 / the current content
        :return: 有送出時為 ``True`` / ``True`` when the notification was sent
        """
        if self._file_path is None:
            return False
        self._version = 1
        return self._send(notification("textDocument/didOpen", {
            "textDocument": {
                "uri": file_uri(self._file_path),
                "languageId": language_id(Path(self._file_path).suffix),
                "version": self._version,
                "text": text,
            }
        }))

    def did_change(self, text: str) -> bool:
        """
        通知伺服器內容已變更（整份取代）
        Tell the server the content changed, sending the whole document.

        :param text: 目前內容 / the current content
        :return: 有送出時為 ``True`` / ``True`` when the notification was sent
        """
        if self._file_path is None:
            return False
        self._version += 1
        return self._send(notification("textDocument/didChange", {
            "textDocument": {"uri": file_uri(self._file_path), "version": self._version},
            "contentChanges": [{"text": text}],
        }))

    def request_completion(self, line: int, column: int) -> bool:
        """
        要求某個位置的補全候選
        Ask for the completions at a position.

        :param line: 以 0 起算的行號 / the 0-based line
        :param column: 以 0 起算的欄位 / the 0-based column
        :return: 有送出時為 ``True`` / ``True`` when the request was sent
        """
        if self._file_path is None:
            return False
        request_id = self._take_id()
        self._pending_completion_id = request_id
        return self._send_request(request(request_id, "textDocument/completion", {
            "textDocument": {"uri": file_uri(self._file_path)},
            "position": {"line": line, "character": column},
        }))

    def request_hover(self, line: int, column: int) -> bool:
        """
        要求某個位置的說明
        Ask for the description of what is at a position.

        :param line: 以 0 起算的行號 / the 0-based line
        :param column: 以 0 起算的欄位 / the 0-based column
        :return: 有送出時為 ``True`` / ``True`` when the request was sent
        """
        return self._position_request(
            "textDocument/hover", line, column, "_pending_hover_id")

    def request_rename(self, line: int, column: int, new_name: str) -> bool:
        """
        要求把某個位置的符號重新命名
        Ask to rename the symbol at a position.

        :param line: 以 0 起算的行號 / the 0-based line
        :param column: 以 0 起算的欄位 / the 0-based column
        :param new_name: 新名稱 / the new name
        :return: 有送出時為 ``True`` / ``True`` when the request was sent
        """
        if self._file_path is None or not new_name:
            return False
        request_id = self._take_id()
        self._pending_edit_id = request_id
        return self._send_request(request(request_id, "textDocument/rename", {
            "textDocument": {"uri": file_uri(self._file_path)},
            "position": {"line": line, "character": column},
            "newName": new_name,
        }))

    def request_formatting(self, tab_size: int = 4) -> bool:
        """
        要求格式化整份檔案
        Ask the server to format the whole file.

        :param tab_size: 縮排寬度 / the indent width to format with
        :return: 有送出時為 ``True`` / ``True`` when the request was sent
        """
        if self._file_path is None:
            return False
        request_id = self._take_id()
        self._pending_edit_id = request_id
        return self._send_request(request(request_id, "textDocument/formatting", {
            "textDocument": {"uri": file_uri(self._file_path)},
            "options": {"tabSize": tab_size, "insertSpaces": True},
        }))

    def request_definition(self, line: int, column: int) -> bool:
        """
        要求某個位置的定義位置
        Ask where the symbol at a position is defined.

        :param line: 以 0 起算的行號 / the 0-based line
        :param column: 以 0 起算的欄位 / the 0-based column
        :return: 有送出時為 ``True`` / ``True`` when the request was sent
        """
        return self._position_request("textDocument/definition", line, column, "_pending_definition_id")

    def _position_request(
            self, method: str, line: int, column: int, pending_attribute: str) -> bool:
        """送出一則以游標位置為參數的請求 / Send one request about a caret position."""
        if self._file_path is None:
            return False
        request_id = self._take_id()
        setattr(self, pending_attribute, request_id)
        return self._send_request(request(request_id, method, {
            "textDocument": {"uri": file_uri(self._file_path)},
            "position": {"line": line, "character": column},
        }))

    def handle_message(self, message: dict) -> None:
        """
        處理伺服器送來的一則訊息
        Handle one message from the server.

        :param message: 已解析的訊息 / the parsed message
        """
        if message.get("method") == "textDocument/publishDiagnostics":
            entries = diagnostic_entries(message.get("params"))
            self.diagnostics_ready.emit(entries)
            return
        if "result" not in message:
            return
        if message.get("id") == self._pending_completion_id:
            self._pending_completion_id = None
            self.completions_ready.emit(completion_labels(message.get("result")))
            return
        if message.get("id") == self._pending_definition_id:
            self._pending_definition_id = None
            location = definition_location(message.get("result"))
            if location is not None:
                self.definition_ready.emit(location)
            return
        if message.get("id") == self._pending_hover_id:
            self._pending_hover_id = None
            text = hover_text(message.get("result"))
            if text:
                self.hover_ready.emit(text)
            return
        if message.get("id") == self._pending_edit_id:
            self._pending_edit_id = None
            uri = file_uri(self._file_path) if self._file_path else ""
            edits = text_edits(message.get("result"), uri)
            if edits:
                self.edits_ready.emit(edits)

    def stop(self) -> None:
        """
        放掉這個檔案的連線
        Let go of this file's connection.

        伺服器是共用的，所以這裡只通知它這個檔案關了；等到沒有任何編輯器還用著同
        一個伺服器，連線表才會把程序關掉。
        The server is shared, so this only tells it the file is closed; the
        process is shut down once no editor is using that server any more.
        """
        session, self._session = self._session, None
        self._pending_completion_id = None
        self._pending_definition_id = None
        self._pending_hover_id = None
        self._pending_edit_id = None
        if session is None:
            return
        if self._file_path is not None:
            uri = file_uri(self._file_path)
            session.send(notification("textDocument/didClose", {"textDocument": {"uri": uri}}))
            session.forget_document(uri)
        session_registry.release(session)

    def did_save(self, text: str) -> bool:
        """
        通知伺服器檔案已存檔
        Tell the server the file was saved.

        有些伺服器只在存檔後才重跑比較慢的檢查，收不到這個通知就永遠不會跑。
        Some servers only run their slower checks on save, and never run them at
        all without this.

        :param text: 存下去的內容 / the content that was saved
        :return: 有送出時為 ``True`` / ``True`` when the notification was sent
        """
        if self._file_path is None:
            return False
        return self._send(notification("textDocument/didSave", {
            "textDocument": {"uri": file_uri(self._file_path)},
            "text": text,
        }))

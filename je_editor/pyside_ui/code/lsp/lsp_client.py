"""
以 stdio 與語言伺服器溝通
Talk to a language server over stdio.

用 QProcess 而不是自己開執行緒：QProcess 本來就是非同步的，讀到資料會發訊號，
所以不需要為了等待輸出而佔住一條執行緒。
This uses QProcess rather than a thread of its own: QProcess is already
asynchronous and signals when data arrives, so no thread has to sit waiting for
output.

伺服器沒安裝、啟動失敗或中途結束時都只是「沒有補全」，不會影響編輯。
A server that is missing, fails to start, or dies mid-session simply means no
completions; editing carries on.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.lsp.language_servers import language_id, server_command
from je_editor.utils.lsp.lsp_protocol import (
    MessageReader,
    completion_labels,
    diagnostic_entries,
    encode_message,
    file_uri,
    notification,
    request,
)

# 等待伺服器結束的時間（毫秒）/ How long to wait for the server to exit
_SHUTDOWN_WAIT_MS = 2000


class LspClient(QObject):
    """
    一個檔案對應的語言伺服器連線
    One language server connection, for one file.
    """

    completions_ready = Signal(list)  # list[str]
    diagnostics_ready = Signal(list)  # list[dict]

    def __init__(self, parent: QObject | None = None) -> None:
        """
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._process: QProcess | None = None
        self._reader = MessageReader()
        self._next_id = 1
        self._file_path: str | None = None
        self._version = 0
        self._pending_completion_id: int | None = None

    @property
    def running(self) -> bool:
        """伺服器是否正在執行 / Whether the server is running."""
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def start_for(self, file_path: str, servers: dict | None = None) -> bool:
        """
        為某個檔案啟動對應的語言伺服器
        Start the language server that handles a file.

        :param file_path: 檔案路徑 / the file to serve
        :param servers: 伺服器對照表 / the server mapping to consult
        :return: 有啟動時為 ``True`` / ``True`` when a server was started
        """
        command = server_command(Path(file_path).suffix, servers)
        if command is None:
            return False
        self.stop()
        process = QProcess(self)
        process.setProgram(command[0])
        process.setArguments(command[1:])
        process.readyReadStandardOutput.connect(self._read_output)
        process.start()
        if not process.waitForStarted(_SHUTDOWN_WAIT_MS):
            jeditor_logger.debug(f"lsp_client: {command[0]} did not start")
            process.deleteLater()
            return False
        self._process = process
        self._file_path = file_path
        self._send(request(self._take_id(), "initialize", {
            "processId": None,
            "rootUri": file_uri(str(Path(file_path).parent)),
            "capabilities": {},
        }))
        self._send(notification("initialized", {}))
        return True

    def _take_id(self) -> int:
        """取得下一個請求編號 / Take the next request id."""
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def _send(self, payload: dict) -> bool:
        """把訊息寫給伺服器 / Write a message to the server."""
        if not self.running:
            return False
        self._process.write(encode_message(payload))
        return True

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
        return self._send(request(request_id, "textDocument/completion", {
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
        if message.get("id") == self._pending_completion_id and "result" in message:
            self._pending_completion_id = None
            self.completions_ready.emit(completion_labels(message.get("result")))

    def _read_output(self) -> None:
        """讀取伺服器輸出並逐則處理 / Read the server's output and handle each message."""
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput())
        for message in self._reader.feed(data):
            self.handle_message(message)

    def stop(self) -> None:
        """
        結束伺服器
        Shut the server down.

        先以 ``shutdown``/``exit`` 請它自己結束，逾時才強制終止。
        It is asked to finish with ``shutdown``/``exit`` first, and only killed
        if it does not.
        """
        process, self._process = self._process, None
        self._reader = MessageReader()
        self._pending_completion_id = None
        if process is None:
            return
        if process.state() != QProcess.ProcessState.NotRunning:
            process.write(encode_message(request(self._take_id(), "shutdown")))
            process.write(encode_message(notification("exit")))
            if not process.waitForFinished(_SHUTDOWN_WAIT_MS):
                process.kill()
                process.waitForFinished(_SHUTDOWN_WAIT_MS)
        process.deleteLater()

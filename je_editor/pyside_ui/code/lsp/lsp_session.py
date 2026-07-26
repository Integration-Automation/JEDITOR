"""
一個語言伺服器程序，供開著同種檔案的編輯器共用
One language server process, shared by every editor holding that kind of file.

原本是「一個編輯器一個伺服器」，開五個 ``.ts`` 就有五個伺服器程序，各自把整個
專案索引一遍——記憶體與啟動時間都乘以五，而且它們對同一份專案的認知還各自獨立。
It used to be one server per editor, so five open ``.ts`` files meant five
processes each indexing the whole project: five times the memory and the startup
cost, with five separate ideas of the same project.

同一個指令與同一個專案根目錄只會有一個連線，用參考計數決定什麼時候關掉。回覆依
請求編號送回發問的那個客戶端，診斷則依 URI 送給對應的檔案。
One connection exists per command and project root, closed when the last user
lets go. A reply goes back to whichever client asked, and a diagnostic goes to
the client holding that URI.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QObject, QProcess

from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.lsp.lsp_protocol import (
    MessageReader, encode_message, notification, request
)

# 等待伺服器啟動或結束的時間（毫秒）/ How long to wait for the server to start or finish
_WAIT_MS = 2000


class LspSession(QObject):
    """
    一個語言伺服器連線
    One connection to a language server.
    """

    def __init__(self, command: List[str], root: str, parent: QObject | None = None) -> None:
        """
        :param command: 啟動伺服器的指令 / the command that starts the server
        :param root: 專案根目錄 / the project root it serves
        :param parent: Qt 父物件 / the Qt parent
        """
        super().__init__(parent)
        self._command = list(command)
        self._root = root
        self._process: QProcess | None = None
        self._reader = MessageReader()
        self._next_id = 1
        # 每個請求編號屬於哪個客戶端 / Which client each request id belongs to
        self._waiting: Dict[int, object] = {}
        # 目前開著的檔案，URI 對應客戶端 / The open files, by URI
        self._documents: Dict[str, object] = {}

    @property
    def running(self) -> bool:
        """伺服器是否正在執行 / Whether the server is running."""
        return (self._process is not None
                and self._process.state() != QProcess.ProcessState.NotRunning)

    @property
    def key(self) -> Tuple[Tuple[str, ...], str]:
        """這個連線的識別 / What identifies this connection."""
        return tuple(self._command), self._root

    def start(self, root_uri: str) -> bool:
        """
        啟動伺服器
        Start the server.

        :param root_uri: 專案根目錄的 URI / the project root's URI
        :return: 有啟動時為 ``True`` / ``True`` when it started
        """
        if self.running:
            return True
        process = QProcess(self)
        process.setProgram(self._command[0])
        process.setArguments(self._command[1:])
        process.readyReadStandardOutput.connect(self._read_output)
        process.start()
        if not process.waitForStarted(_WAIT_MS):
            jeditor_logger.debug(f"lsp_session: {self._command[0]} did not start")
            process.deleteLater()
            return False
        self._process = process
        self.send(request(self.take_id(), "initialize", {
            "processId": None,
            "rootUri": root_uri,
            "capabilities": {},
        }))
        self.send(notification("initialized", {}))
        return True

    def take_id(self) -> int:
        """取得下一個請求編號 / Take the next request id."""
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def send(self, payload: dict) -> bool:
        """把訊息寫給伺服器 / Write a message to the server."""
        if not self.running:
            return False
        self._process.write(encode_message(payload))
        return True

    def send_request(self, client: object, payload: dict) -> bool:
        """
        代表某個客戶端送出請求，回覆會送回給它
        Send a request on a client's behalf, so the reply comes back to it.

        :param client: 發問的客戶端 / the client asking
        :param payload: 請求內容 / the request
        :return: 有送出時為 ``True`` / ``True`` when it was sent
        """
        if not self.send(payload):
            return False
        self._waiting[payload.get("id")] = client
        return True

    def register_document(self, uri: str, client: object) -> None:
        """記下某個檔案由哪個客戶端負責 / Note which client holds a file."""
        self._documents[uri] = client

    def forget_document(self, uri: str) -> None:
        """放掉一個檔案 / Let go of a file."""
        self._documents.pop(uri, None)

    @property
    def user_count(self) -> int:
        """目前有幾個客戶端在用 / How many clients are using this."""
        return len(self._documents)

    def _read_output(self) -> None:
        """讀取伺服器輸出並逐則轉交 / Read the server's output and pass each message on."""
        if self._process is None:
            return
        data = bytes(self._process.readAllStandardOutput())
        for message in self._reader.feed(data):
            self.route(message)

    def route(self, message: dict) -> Optional[object]:
        """
        把一則訊息交給該收的客戶端
        Hand one message to the client it belongs to.

        診斷帶著 URI，交給持有該檔案的客戶端；其餘依請求編號交回發問的那一個。
        A diagnostic carries a URI and goes to whoever holds that file; anything
        else goes back to whichever client asked for it.

        :param message: 已解析的訊息 / the parsed message
        :return: 收下這則訊息的客戶端，沒有時為 ``None`` / the client, or ``None``
        """
        if message.get("method") == "textDocument/publishDiagnostics":
            uri = (message.get("params") or {}).get("uri", "")
            client = self._documents.get(uri)
        else:
            client = self._waiting.pop(message.get("id"), None)
        if client is not None:
            client.handle_message(message)
        return client

    def shutdown(self) -> None:
        """
        結束伺服器
        Shut the server down.

        先以 ``shutdown``/``exit`` 請它自己結束，逾時才強制終止。
        It is asked to finish with ``shutdown``/``exit`` first, and only killed
        if it does not.
        """
        process, self._process = self._process, None
        self._reader = MessageReader()
        self._waiting = {}
        self._documents = {}
        if process is None:
            return
        if process.state() != QProcess.ProcessState.NotRunning:
            process.write(encode_message(request(self.take_id(), "shutdown")))
            process.write(encode_message(notification("exit")))
            if not process.waitForFinished(_WAIT_MS):
                process.kill()
                process.waitForFinished(_WAIT_MS)
        process.deleteLater()


class LspSessionRegistry:
    """
    保管目前開著的語言伺服器連線
    Keep the language server connections that are currently open.
    """

    def __init__(self) -> None:
        self._sessions: Dict[Tuple[Tuple[str, ...], str], LspSession] = {}

    def session_for(self, command: List[str], root: str, root_uri: str) -> Optional[LspSession]:
        """
        取得對應的連線，沒有就開一個
        The connection for a command and root, starting one when there is none.

        :param command: 啟動伺服器的指令 / the command that starts the server
        :param root: 專案根目錄 / the project root
        :param root_uri: 專案根目錄的 URI / that root as a URI
        :return: 連線，啟動失敗時為 ``None`` / the session, or ``None`` when it failed
        """
        key = (tuple(command), root)
        session = self._sessions.get(key)
        if session is not None and session.running:
            return session
        session = LspSession(command, root)
        if not session.start(root_uri):
            return None
        self._sessions[key] = session
        return session

    def release(self, session: LspSession) -> bool:
        """
        放掉一個連線；沒有人在用就關掉伺服器
        Let go of a connection, shutting the server down once nobody holds it.

        :param session: 要放掉的連線 / the session being let go
        :return: 是否關掉了伺服器 / whether the server was shut down
        """
        if session.user_count > 0:
            return False
        self._sessions.pop(session.key, None)
        session.shutdown()
        return True

    def sessions(self) -> List[LspSession]:
        """目前開著的連線 / The connections currently open."""
        return list(self._sessions.values())

    def shutdown_all(self) -> None:
        """關掉每一個連線 / Shut every connection down."""
        for session in list(self._sessions.values()):
            session.shutdown()
        self._sessions = {}


# 整個應用程式共用的連線表 / The connections the whole application shares
session_registry = LspSessionRegistry()

"""
以 TCP 連線收發除錯協定訊息
Debug protocol messages over a TCP connection.

啟動程式時，除錯轉接器是編輯器自己開的子程序；但接上一個已經在執行的程式時，
對方通常已經帶著轉接器在某個連接埠等著，要做的是直接連過去。這個類別把一條 TCP
連線包成跟「以位元組收發的工作」一樣的形狀，除錯工作階段就不必分辨兩者。之後
經過 SSH 轉送的遠端除錯用的也是它。
When a program is launched, the debug adapter is a child process the editor
starts. When attaching to a program that is already running, the other side
usually has its adapter waiting on a port already, and what has to be done is
connect to it. This class gives a TCP connection the same shape as a task that
exchanges bytes, so the debug session need not tell the two apart. Remote
debugging through a port forwarded over SSH uses it as well.
"""
from __future__ import annotations

import socket
import threading

from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import OutputStream, TaskSpec, TaskState
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 連線最多等幾秒 / Seconds to wait for the connection at most
CONNECT_TIMEOUT_SECONDS = 5.0
_READ_SIZE = 65536
_SCHEME = "tcp"


class SocketChannel:
    """
    一條收發位元組的 TCP 連線，形狀跟位元組模式的工作一樣
    A TCP connection exchanging bytes, shaped like a task in binary mode.
    """

    def __init__(self, host: str, port: int) -> None:
        """
        :param host: 要連到的主機 / the host to connect to
        :param port: 要連到的連接埠 / the port to connect to
        """
        self._address = (host, port)
        self._spec = TaskSpec((_SCHEME, f"{host}:{port}"), name=f"{_SCHEME}://{host}:{port}", binary=True)
        self._output = EventHook()
        self._finished = EventHook()
        self._state = TaskState.PENDING
        self._socket: socket.socket | None = None
        self._lock = threading.Lock()
        self._exit_code: int | None = None

    @property
    def spec(self) -> TaskSpec:
        """這條連線連到哪裡 / Where this connection goes."""
        return self._spec

    @property
    def output(self) -> EventHook:
        """收到資料時發出，引數是 ``OutputStream.STDOUT`` 與位元組 / Fired with ``OutputStream.STDOUT`` and the bytes received."""
        return self._output

    @property
    def finished(self) -> EventHook:
        """連線結束後發出，引數是零 / Fired with zero once the connection has ended."""
        return self._finished

    def state(self) -> TaskState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """
        return self._state

    def exit_code(self) -> int | None:
        """
        連線結束了沒有
        Whether the connection has ended.

        :return: 結束後為零，還連著時為 ``None`` / zero once it ended, ``None`` while connected
        """
        return self._exit_code

    def start(self) -> bool:
        """
        連線
        Connect.

        :return: 連上時為 ``True``；連不上或已經連過時為 ``False``
            ``True`` when connected, ``False`` when it could not or already had
        """
        if self._state is not TaskState.PENDING:
            return False
        try:
            connection = socket.create_connection(self._address, CONNECT_TIMEOUT_SECONDS)
        except OSError as error:
            jeditor_logger.info("could not connect to %s: %s", self._spec.name, error)
            self._state = TaskState.FAILED_TO_START
            return False
        connection.settimeout(None)
        self._socket = connection
        self._state = TaskState.RUNNING
        threading.Thread(target=self._read, name="SocketChannel-read", daemon=True).start()
        return True

    def write(self, text: str | bytes) -> bool:
        """
        送出資料
        Send data.

        :param text: 要送出的位元組或文字 / the bytes or text to send
        :return: 有送出時為 ``True`` / ``True`` when it was sent
        """
        connection = self._socket
        if connection is None or self._state is not TaskState.RUNNING:
            return False
        data = text.encode("utf-8") if isinstance(text, str) else text
        try:
            with self._lock:
                connection.sendall(data)
        except OSError as error:
            jeditor_logger.debug("sending to %s failed: %s", self._spec.name, error)
            return False
        return True

    def close_input(self) -> None:
        """
        告訴對方不會再送資料，但繼續接收
        Tell the other side nothing more will be sent, while still receiving.
        """
        connection = self._socket
        if connection is None or self._state is not TaskState.RUNNING:
            return
        try:
            connection.shutdown(socket.SHUT_WR)
        except OSError as error:
            jeditor_logger.debug("closing the sending side of %s: %s", self._spec.name, error)

    def cancel(self) -> None:
        """
        關閉連線
        Close the connection.
        """
        connection = self._socket
        if connection is None or self._state is not TaskState.RUNNING:
            return
        self._state = TaskState.CANCELLED
        try:
            connection.shutdown(socket.SHUT_RDWR)
        except OSError as error:
            # 對方已經先關了 / The other side closed first
            jeditor_logger.debug("shutting down %s: %s", self._spec.name, error)
        connection.close()

    def _read(self) -> None:
        """把連線讀到結束，讀到什麼就通知什麼 / Read the connection to its end, passing on what is read."""
        connection = self._socket
        while connection is not None:
            try:
                data = connection.recv(_READ_SIZE)
            except OSError:
                break
            if not data:
                break
            self._output.emit(OutputStream.STDOUT, data)
        if self._state is TaskState.RUNNING:
            self._state = TaskState.FINISHED
            if connection is not None:
                connection.close()
        self._exit_code = 0
        self._finished.emit(0)

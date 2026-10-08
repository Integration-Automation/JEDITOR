"""
遠端工作階段的介面
The interface for a remote session.

工作區的根目錄可以在另一台機器上。服務只認得「一個可以連線、可以在上面讀寫檔案、
執行工作、轉送連接埠的工作階段」，不認得 SSH 或其他傳輸方式——那些是傳輸實作自己
的事，所以這裡沒有任何一個名稱提到 SSH。
A workspace root may be on another machine. A service knows one session that can
connect, read and write files, run tasks and forward ports, never SSH or any
other transport. Those stay the business of the transport that implements this,
which is why no name here mentions SSH.

在遠端執行程序用的是跟本機一樣的 ``TaskRunner``，所以語言伺服器與除錯轉接器換成
遠端的執行器就能在遠端啟動，呼叫的人不必分辨。
A process on the remote machine is run through the same ``TaskRunner`` as a local
one, so a language server or a debug adapter starts remotely by being given the
remote runner, and the caller never has to tell.

檔案系統與探索的呼叫都會等對方回答，要從工作執行緒呼叫，不要在畫面執行緒上等。
File-system and discovery calls wait for the other side to answer: call them from
a worker thread, never wait on the widget thread.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import TaskRunner


class RemoteState(Enum):
    """
    遠端工作階段的狀態
    The state a remote session is in.
    """

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass(frozen=True)
class RemoteEntry:
    """
    遠端檔案系統裡的一個項目
    One entry of a remote file system.

    :param name: 名稱，不含目錄 / its name, without the directory
    :param path: 在遠端機器上的完整路徑 / its full path on the remote machine
    :param is_directory: 是不是目錄 / whether it is a directory
    :param size: 位元組數，目錄為零 / its size in bytes, zero for a directory
    :param modified: 最後修改時間（自 epoch 起的秒數）/ when it was last modified, in seconds since the epoch
    """

    name: str
    path: str
    is_directory: bool = False
    size: int = 0
    modified: float = 0.0


@dataclass(frozen=True)
class RemoteInterpreter:
    """
    在遠端機器上找到的一個直譯器
    An interpreter found on the remote machine.

    :param path: 直譯器在遠端機器上的路徑 / the interpreter's path on the remote machine
    :param version: 版本，例如 ``3.12.4`` / its version, such as ``3.12.4``
    """

    path: str
    version: str = ""


@runtime_checkable
class RemoteFileSystem(Protocol):
    """
    遠端機器的檔案系統
    The file system of the remote machine.

    路徑一律是遠端機器上的絕對路徑。做不到的操作丟 ``JEditorServiceException``。
    Paths are always absolute paths on the remote machine. An operation that
    cannot be done raises ``JEditorServiceException``.
    """

    def read_bytes(self, path: str) -> bytes:
        """
        讀出一個檔案的內容
        Read a file's content.

        :param path: 檔案路徑 / the file's path
        :return: 內容 / the content
        :raises JEditorServiceException: 讀不到 / when it cannot be read
        """

    def write_bytes(self, path: str, data: bytes) -> None:
        """
        寫入一個檔案，原本的內容整個換掉
        Write a file, replacing whatever it held.

        :param path: 檔案路徑 / the file's path
        :param data: 要寫入的內容 / the content to write
        :raises JEditorServiceException: 寫不進去 / when it cannot be written
        """

    def list_directory(self, path: str) -> tuple[RemoteEntry, ...]:
        """
        列出一個目錄裡的項目
        List the entries of a directory.

        :param path: 目錄路徑 / the directory's path
        :return: 項目，目錄在前、依名稱排序 / the entries, directories first, sorted by name
        :raises JEditorServiceException: 列不出來 / when it cannot be listed
        """

    def stat(self, path: str) -> RemoteEntry | None:
        """
        查詢一個路徑
        Look a path up.

        :param path: 路徑 / the path
        :return: 那個項目，不存在時為 ``None`` / the entry, or ``None`` when there is none
        :raises JEditorServiceException: 問不到遠端 / when the remote cannot be asked
        """


@runtime_checkable
class PortForward(Protocol):
    """
    一條轉送中的連接埠：連到本機的埠，就等於連到遠端的埠
    One port being forwarded: connecting to the local port reaches the remote one.
    """

    @property
    def local_port(self) -> int:
        """本機這一端的連接埠 / The port on this machine."""

    @property
    def remote_port(self) -> int:
        """遠端那一端的連接埠 / The port on the remote side."""

    def is_open(self) -> bool:
        """
        是否還在轉送
        Whether it is still forwarding.

        :return: 還在轉送時為 ``True`` / ``True`` while it forwards
        """

    def close(self) -> None:
        """
        停止轉送
        Stop forwarding.
        """


@runtime_checkable
class RemoteSession(Protocol):
    """
    一條到遠端機器的連線
    One connection to a remote machine.
    """

    @property
    def authority(self) -> str:
        """連到哪裡，也就是根目錄 URI 裡的主機部分 / Where it connects to: the host part of a root's URI."""

    @property
    def state_changed(self) -> EventHook:
        """狀態改變後發出，引數是新的 :class:`RemoteState` / Fired with the new state."""

    def state(self) -> RemoteState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """

    def last_error(self) -> str:
        """
        最近一次連線失敗的原因
        Why the last attempt to connect failed.

        :return: 給使用者看的說明，沒有失敗時為空字串 / text to show the user, empty when nothing failed
        """

    def connect(self) -> bool:
        """
        建立連線
        Open the connection.

        :return: 有連上時為 ``True`` / ``True`` when it connected
        """

    def reconnect(self) -> bool:
        """
        連線斷了之後再連一次
        Connect again after the connection was lost.

        :return: 有連上時為 ``True`` / ``True`` when it connected
        """

    def disconnect(self) -> None:
        """
        中斷連線並放掉它持有的資源
        Close the connection and release what it holds.
        """

    def task_runner(self) -> TaskRunner:
        """
        取得在遠端機器上執行工作的地方
        Somewhere tasks run on the remote machine.

        跟本機的執行器是同一個介面，所以呼叫的人不必分辨程序在哪裡執行。
        It is the same interface as the local runner, so a caller never has to
        tell where a process runs.

        :return: 遠端的工作執行器 / the remote task runner
        """

    def file_system(self) -> RemoteFileSystem:
        """
        取得遠端機器的檔案系統
        The remote machine's file system.

        :return: 檔案系統 / the file system
        """

    def forward_port(self, remote_port: int, remote_host: str = "127.0.0.1",
                     local_port: int = 0) -> PortForward:
        """
        把遠端的一個連接埠轉送到本機
        Forward a port of the remote side to this machine.

        :param remote_port: 遠端的連接埠 / the port on the remote side
        :param remote_host: 從遠端機器看出去的主機，預設是它自己
            the host as seen from the remote machine, itself by default
        :param local_port: 本機要用的連接埠，零表示隨便挑一個空的
            the local port to use, zero to pick a free one
        :return: 轉送的把手 / the handle of the forward
        :raises JEditorServiceException: 轉送建立不起來 / when the forward cannot be set up
        """

    def interpreters(self, root: str = "") -> tuple[RemoteInterpreter, ...]:
        """
        找出遠端機器上可以用的 Python 直譯器
        Find the Python interpreters available on the remote machine.

        :param root: 專案目錄；給了就連它底下的虛擬環境一起找
            a project directory, whose virtual environments are looked at too when given
        :return: 找到的直譯器，專案自己的在前 / the interpreters found, the project's own first
        """


# 依 authority 建立一條遠端工作階段 / Builds a remote session for an authority
RemoteTransport = Callable[[str], RemoteSession]

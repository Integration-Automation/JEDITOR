"""
遠端工作階段的介面
The interface for a remote session.

工作區的根目錄之後可以在另一台機器上。服務只認得「一個可以連線、可以在上面執行
工作的工作階段」，不認得 SSH 或其他傳輸方式——那些是傳輸實作自己的事。
A workspace root may later be on another machine. A service knows one session
that can connect and can run tasks, never SSH or any other transport, which stay
the business of the transport that implements this.

遠端檔案系統、連接埠轉送與直譯器探索要等遠端開發那個里程碑，這裡先固定連線的
生命週期。
The remote file system, port forwarding and interpreter discovery wait for the
remote development milestone; this fixes the connection's lifecycle first.
"""
from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import TaskRunner


class RemoteState(Enum):
    """
    遠端連線的狀態
    The state a remote connection is in.
    """

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


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

    def connect(self) -> bool:
        """
        建立連線
        Open the connection.

        :return: 有連上時為 ``True`` / ``True`` when it connected
        """

    def disconnect(self) -> None:
        """
        中斷連線並放掉它持有的資源
        Close the connection and release what it holds.
        """

    def task_runner(self) -> TaskRunner:
        """
        取得在遠端執行工作的執行器
        The runner that runs tasks on the remote machine.

        跟本機的執行器是同一個介面，呼叫端不必分辨程序在哪裡。
        It has the interface the local runner has, so a caller never has to tell
        where a process runs.

        :return: 工作執行器 / the task runner
        """


# 由主機部分建立一條連線；登記時的名稱是 URI 的 scheme
# Builds a session from an authority; it is registered under the URI scheme it serves
RemoteTransport = Callable[[str], RemoteSession]

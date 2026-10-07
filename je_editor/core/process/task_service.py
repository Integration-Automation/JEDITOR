"""
執行外部程式的介面
The interface for running an external program.

執行使用者的程式、啟動語言伺服器或除錯轉接器，都是「啟動一個程序、讀它的輸出、
等它結束」。把這件事變成介面之後，程序在本機還是在遠端對呼叫端就沒有差別。
Running the user's program, starting a language server and starting a debug
adapter are all one thing: start a process, read its output, wait for it to end.
Behind an interface, the caller no longer cares whether that process is on this
machine or a remote one.

這裡只有介面與資料物件，不啟動任何程序。
This holds the interface and its data objects only, and starts no process.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.utils.exception.exceptions import JEditorServiceException


class TaskState(Enum):
    """
    一個工作的狀態
    The state a task is in.
    """

    PENDING = "pending"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED_TO_START = "failed_to_start"
    CANCELLED = "cancelled"


class OutputStream(Enum):
    """
    輸出來自哪一個串流
    Which stream a piece of output came from.
    """

    STDOUT = "stdout"
    STDERR = "stderr"


@dataclass(frozen=True)
class TaskSpec:
    """
    要執行什麼
    What to run.

    指令一律是引數清單，沒有「一整行交給 shell」的形式，所以檔名裡的空白或引號
    不會被當成指令的一部分。
    The command is always a list of arguments and there is no form that hands a
    whole line to a shell, so a space or a quote in a file name can never become
    part of the command.

    :param command: 程式與它的引數 / the program and its arguments
    :param working_directory: 工作目錄，空字串表示沿用目前的
        the working directory, empty to keep the current one
    :param environment: 要加上或覆寫的環境變數 / environment variables to add or override
    :param name: 給使用者看的名稱 / the name to show the user
    :param binary: 為真時輸出以讀到的位元組原樣送出、寫入也收位元組；給除錯轉接器
        這種以位元組組框的協定用
        when true, output is delivered as the bytes that were read and writes
        take bytes: for protocols framed in bytes, such as a debug adapter's
    :raises JEditorServiceException: 指令是空的，或裡面有不是字串的項目
        when the command is empty or holds something that is not a string
    """

    command: tuple[str, ...]
    working_directory: str = ""
    environment: Mapping[str, str] = field(default_factory=dict)
    name: str = ""
    binary: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.command, str) or not self.command:
            raise JEditorServiceException("A task command has to be a non-empty list of arguments")
        if not all(isinstance(part, str) and part for part in self.command):
            raise JEditorServiceException("Every part of a task command has to be a non-empty string")
        # 複製並凍結，之後就不會被呼叫端改掉 / Copy and freeze, so the caller cannot change them later
        object.__setattr__(self, "command", tuple(self.command))
        object.__setattr__(self, "environment", MappingProxyType(dict(self.environment)))


@runtime_checkable
class TaskHandle(Protocol):
    """
    一個準備好或正在執行的工作
    One task that is ready to run or is running.

    先訂閱輸出再呼叫 :meth:`start`，才不會漏掉一開始的輸出。
    Subscribe to the output before calling :meth:`start`, so none of the early
    output is missed.
    """

    @property
    def spec(self) -> TaskSpec:
        """這個工作要執行什麼 / What this task runs."""

    @property
    def output(self) -> EventHook:
        """
        有輸出時發出，引數是 :class:`OutputStream` 與內容
        Fired with the stream and what was read.

        內容是文字；工作是 ``binary`` 時則是位元組。訂閱者在讀取輸出的執行緒上被呼叫。
        What was read is text, or bytes for a ``binary`` task. Subscribers are
        called on the thread that reads the output.
        """

    @property
    def finished(self) -> EventHook:
        """結束後發出，引數是結束代碼 / Fired with the exit code once it ends."""

    def state(self) -> TaskState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """

    def exit_code(self) -> int | None:
        """
        結束代碼
        The exit code.

        :return: 結束代碼，還沒結束時為 ``None`` / the code, or ``None`` while it runs
        """

    def start(self) -> bool:
        """
        啟動程序
        Start the process.

        :return: 有啟動時為 ``True`` / ``True`` when it started
        """

    def write(self, text: str | bytes) -> bool:
        """
        寫到程序的標準輸入
        Write to the process's standard input.

        :param text: 要寫入的文字；工作是 ``binary`` 時給位元組
            the text to write, or bytes for a ``binary`` task
        :return: 有寫入時為 ``True`` / ``True`` when it was written
        """

    def cancel(self) -> None:
        """
        結束程序
        Stop the process.
        """


@runtime_checkable
class TaskRunner(Protocol):
    """
    能執行工作的地方
    Somewhere tasks can run.
    """

    def create(self, spec: TaskSpec) -> TaskHandle:
        """
        準備一個工作，但還不啟動
        Prepare a task without starting it.

        :param spec: 要執行什麼 / what to run
        :return: 這個工作的把手 / the handle for the task
        """

    def shutdown(self) -> None:
        """
        結束所有還在執行的工作
        Stop every task that is still running.
        """

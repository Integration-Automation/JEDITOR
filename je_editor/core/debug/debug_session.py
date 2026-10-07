"""
除錯工作階段的介面
The interface for a debug session.

除錯面板只該知道「一個可以啟動、暫停、逐步執行的工作階段」，不該知道背後是 pdb
還是哪一個 Debug Adapter Protocol 伺服器。這裡的名稱與資料跟 DAP 的概念對應，
所以之後接上 DAP 不必改介面。
The debug panel should know one session it can launch, pause and step, never
whether pdb or some Debug Adapter Protocol server is behind it. The names and
data here follow DAP's concepts, so connecting DAP later needs no change to the
interface.

堆疊、變數與運算式求值的查詢要等 DAP 那個里程碑決定非同步的形式，這裡先固定
控制指令與資料物件。
Queries for the stack, variables and expression evaluation wait for the DAP
milestone to settle how they answer asynchronously; this fixes the control
commands and the data objects first.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.utils.exception.exceptions import JEditorServiceException


class DebugState(Enum):
    """
    除錯工作階段的狀態
    The state a debug session is in.
    """

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    TERMINATED = "terminated"


class StepKind(Enum):
    """
    逐步執行的方式
    The ways to step.
    """

    OVER = "over"
    INTO = "into"
    OUT = "out"


@dataclass(frozen=True)
class Breakpoint:
    """
    一個中斷點
    One breakpoint.

    :param uri: 所在資源的 URI / the URI of the resource it is in
    :param line: 1 起算的行號 / the 1-based line
    :param condition: 成立才停下來的條件，空字串表示一律停
        the condition that has to hold to stop, empty to stop every time
    :param enabled: 是否啟用 / whether it is in effect
    """

    uri: str
    line: int
    condition: str = ""
    enabled: bool = True


@dataclass(frozen=True)
class StackFrame:
    """
    呼叫堆疊裡的一層
    One frame of the call stack.

    :param frame_id: 轉接器給這一層的編號 / the id the adapter gives this frame
    :param name: 函式名稱 / the function's name
    :param uri: 原始碼的 URI / the URI of the source
    :param line: 1 起算的行號 / the 1-based line
    :param column: 1 起算的欄號 / the 1-based column
    """

    frame_id: int
    name: str
    uri: str
    line: int
    column: int = 1


@dataclass(frozen=True)
class Variable:
    """
    一個變數
    One variable.

    :param name: 變數名稱 / the variable's name
    :param value: 顯示用的值 / the value, as text to show
    :param type_name: 型別名稱 / the name of its type
    :param children_reference: 用來查子項目的編號，零表示沒有子項目
        the handle for asking for its children, zero when it has none
    """

    name: str
    value: str
    type_name: str = ""
    children_reference: int = 0


@dataclass(frozen=True)
class DebugLaunchRequest:
    """
    啟動一次除錯所需的資訊
    What it takes to launch a debug run.

    :param program: 要除錯的程式 / the program to debug
    :param arguments: 交給程式的引數 / the arguments for the program
    :param working_directory: 工作目錄，空字串表示沿用目前的
        the working directory, empty to keep the current one
    :param stop_on_entry: 是否一進入程式就停下來 / whether to stop on the first line
    :raises JEditorServiceException: 沒有指定程式 / when no program is given
    """

    program: str
    arguments: tuple[str, ...] = ()
    working_directory: str = ""
    stop_on_entry: bool = False

    def __post_init__(self) -> None:
        if not self.program:
            raise JEditorServiceException("A debug launch needs a program")


@runtime_checkable
class DebugSession(Protocol):
    """
    一個除錯工作階段
    One debug session.
    """

    @property
    def state_changed(self) -> EventHook:
        """狀態改變後發出，引數是新的 :class:`DebugState` / Fired with the new state."""

    def state(self) -> DebugState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """

    def launch(self, request: DebugLaunchRequest) -> bool:
        """
        啟動程式並開始除錯
        Launch the program under the debugger.

        :param request: 啟動所需的資訊 / what to launch
        :return: 有啟動時為 ``True`` / ``True`` when it started
        """

    def set_breakpoints(self, uri: str, breakpoints: Sequence[Breakpoint]) -> None:
        """
        設定某個資源的全部中斷點
        Set every breakpoint of one resource.

        每次都給整份清單，沒列出的就是清掉——跟 DAP 的 ``setBreakpoints`` 一樣。
        The whole list is given each time and anything left out is cleared, as
        DAP's ``setBreakpoints`` works.

        :param uri: 資源的 URI / the resource's URI
        :param breakpoints: 這個資源現在所有的中斷點 / all its breakpoints now
        """

    def resume(self) -> None:
        """
        繼續執行
        Carry on running.
        """

    def pause(self) -> None:
        """
        暫停執行
        Pause the run.
        """

    def step(self, kind: StepKind) -> None:
        """
        逐步執行
        Take one step.

        :param kind: 逐步的方式 / how to step
        """

    def terminate(self) -> None:
        """
        結束除錯並放掉它持有的程序
        End the run and release the process it holds.
        """


# 建立一個新的除錯工作階段 / Builds one new debug session
DebugSessionFactory = Callable[[], DebugSession]

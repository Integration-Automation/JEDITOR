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

控制指令（繼續、暫停、逐步）送出就回來；查詢（執行緒、堆疊、變數、求值）則給一個
收回覆的函式，答案好了再呼叫它，跟語言服務的發問形式一樣。回覆與事件都在工作階段
自己的執行緒上送達，要更新畫面的人得自己轉回畫面執行緒。
Control commands, resume, pause and step, return as soon as they are sent. A
query, for threads, the stack, variables or an evaluation, takes a function for
the reply and calls it once the answer is there, the same shape language
services use. Replies and events arrive on the session's own thread, and whoever
updates widgets moves them to the widget thread.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar, runtime_checkable

from je_editor.core.events.event_hook import EventHook
from je_editor.utils.exception.exceptions import JEditorServiceException


MAX_PORT = 65535


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
class DebugThread:
    """
    被除錯的程式裡的一條執行緒
    One thread of the program being debugged.

    :param thread_id: 轉接器給它的編號 / the id the adapter gives it
    :param name: 執行緒名稱 / the thread's name
    """

    thread_id: int
    name: str = ""


@dataclass(frozen=True)
class Scope:
    """
    一層堆疊裡的一組變數，例如區域變數或全域變數
    One group of variables in a frame, such as the locals or the globals.

    :param name: 這一組的名稱 / the group's name
    :param variables_reference: 用來查這一組變數的編號 / the handle for asking for its variables
    :param expensive: 取得這一組是否很花時間，花時間的不該自動展開
        whether fetching it is slow, in which case it should not be expanded unasked
    """

    name: str
    variables_reference: int
    expensive: bool = False


@dataclass(frozen=True)
class StopEvent:
    """
    程式停下來了
    The program has stopped.

    :param reason: 為什麼停，例如 ``breakpoint``、``step``、``exception``、``pause``、``entry``
        why, such as ``breakpoint``, ``step``, ``exception``, ``pause`` or ``entry``
    :param thread_id: 停下來的執行緒 / the thread that stopped
    :param description: 給使用者看的說明 / a description to show the user
    :param text: 進一步的文字，例外時是例外的名稱 / further text, the exception's name for one
    :param all_threads_stopped: 是否所有執行緒都停了 / whether every thread stopped
    """

    reason: str
    thread_id: int = 0
    description: str = ""
    text: str = ""
    all_threads_stopped: bool = True


@dataclass(frozen=True)
class OutputEvent:
    """
    被除錯的程式或轉接器的一段輸出
    A piece of output from the program being debugged, or from the adapter.

    :param category: ``stdout``、``stderr``、``console`` 等 / ``stdout``, ``stderr``, ``console`` and so on
    :param text: 輸出的文字 / the text
    """

    category: str
    text: str


@dataclass(frozen=True)
class ExceptionInfo:
    """
    程式停在哪一個例外上
    The exception the program stopped on.

    :param exception_id: 例外的型別名稱 / the exception's type name
    :param description: 例外的訊息 / the exception's message
    :param break_mode: 為什麼會停：``always``、``unhandled``、``userUnhandled`` 或 ``never``
        why it broke: ``always``, ``unhandled``, ``userUnhandled`` or ``never``
    :param stack_trace: 轉接器提供的追蹤文字，沒有時為空字串
        the traceback text the adapter supplies, empty when it has none
    """

    exception_id: str
    description: str = ""
    break_mode: str = ""
    stack_trace: str = ""


@dataclass(frozen=True)
class EvaluateResult:
    """
    運算式求值的結果
    The result of evaluating an expression.

    :param value: 顯示用的值 / the value, as text to show
    :param type_name: 型別名稱 / the name of its type
    :param children_reference: 用來查子項目的編號，零表示沒有子項目
        the handle for asking for its children, zero when it has none
    """

    value: str
    type_name: str = ""
    children_reference: int = 0


@dataclass(frozen=True)
class BreakpointStatus:
    """
    轉接器對一個中斷點的回報
    What the adapter reports about one breakpoint.

    :param uri: 所在資源的 URI / the URI of the resource it is in
    :param line: 實際生效的行號（1 起算），可能跟要求的不同
        the 1-based line it took effect on, which may differ from the one asked for
    :param verified: 是否真的設上了 / whether it was really set
    :param message: 沒設上的原因 / why it was not
    """

    uri: str
    line: int
    verified: bool = True
    message: str = ""


Answer = TypeVar("Answer")


@dataclass(frozen=True)
class DebugReply(Generic[Answer]):
    """
    除錯工作階段對一個查詢的回覆
    A debug session's reply to one query.

    :param value: 答案；答不出來時是該查詢的空值（空的 tuple 或 ``None``）
        the answer, or the query's empty value, an empty tuple or ``None``, when there is none
    :param error: 答不出來的原因，答得出來時為空字串
        why there is no answer, empty when there is one
    """

    value: Answer
    error: str = ""

    @property
    def ok(self) -> bool:
        """是否答出來了 / Whether there is an answer."""
        return not self.error


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
    :param interpreter: 用哪個直譯器執行程式，空字串表示由轉接器決定
        the interpreter that runs the program, empty to let the adapter choose
    :param just_my_code: 是否只在使用者自己的程式碼裡停下來與逐步執行
        whether to stop and step in the user's own code only
    :raises JEditorServiceException: 沒有指定程式 / when no program is given
    """

    program: str
    arguments: tuple[str, ...] = ()
    working_directory: str = ""
    stop_on_entry: bool = False
    interpreter: str = ""
    just_my_code: bool = True

    def __post_init__(self) -> None:
        if not self.program:
            raise JEditorServiceException("A debug launch needs a program")


@dataclass(frozen=True)
class DebugAttachRequest:
    """
    接上一個已經在執行、等著除錯器連線的程式
    Attach to a program that is already running and waiting for a debugger.

    :param host: 程式所在的主機 / the host the program is on
    :param port: 它等候連線的連接埠 / the port it listens on
    :param just_my_code: 是否只在使用者自己的程式碼裡停下來與逐步執行
        whether to stop and step in the user's own code only
    :raises JEditorServiceException: 連接埠不在 1 到 65535 之間
        when the port is not between 1 and 65535
    """

    port: int
    host: str = "127.0.0.1"
    just_my_code: bool = True

    def __post_init__(self) -> None:
        if not 0 < self.port <= MAX_PORT:
            raise JEditorServiceException(f"A debug attach needs a port between 1 and {MAX_PORT}")


@runtime_checkable
class DebugSession(Protocol):
    """
    一個除錯工作階段
    One debug session.
    """

    @property
    def state_changed(self) -> EventHook:
        """狀態改變後發出，引數是新的 :class:`DebugState` / Fired with the new state."""

    @property
    def stopped(self) -> EventHook:
        """程式停下來時發出，引數是 :class:`StopEvent` / Fired with a :class:`StopEvent` when the program stops."""

    @property
    def output(self) -> EventHook:
        """有輸出時發出，引數是 :class:`OutputEvent` / Fired with an :class:`OutputEvent`."""

    @property
    def breakpoints_reported(self) -> EventHook:
        """
        轉接器回報中斷點的狀態時發出，引數是一組 :class:`BreakpointStatus`
        Fired with a tuple of :class:`BreakpointStatus` when the adapter reports on breakpoints.
        """

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

    def attach(self, request: DebugAttachRequest) -> bool:
        """
        接上一個已經在執行的程式
        Attach to a program that is already running.

        :param request: 要接上哪裡 / where to attach
        :return: 有開始連線時為 ``True`` / ``True`` when the attach was started
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

    def resume(self, thread_id: int = 0) -> None:
        """
        繼續執行
        Carry on running.

        :param thread_id: 要繼續的執行緒，零表示上次停下來的那一條
            the thread to resume, zero for the one that stopped last
        """

    def pause(self, thread_id: int = 0) -> None:
        """
        暫停執行
        Pause the run.

        :param thread_id: 要暫停的執行緒，零表示上次停下來的那一條
            the thread to pause, zero for the one that stopped last
        """

    def step(self, kind: StepKind, thread_id: int = 0) -> None:
        """
        逐步執行
        Take one step.

        :param kind: 逐步的方式 / how to step
        :param thread_id: 要逐步的執行緒，零表示上次停下來的那一條
            the thread to step, zero for the one that stopped last
        """

    def threads(self, on_reply: Callable[[DebugReply[tuple[DebugThread, ...]]], None]) -> None:
        """
        查詢程式裡的執行緒
        Ask for the program's threads.

        :param on_reply: 收回覆的函式 / receives the reply
        """

    def stack_trace(self, thread_id: int,
                    on_reply: Callable[[DebugReply[tuple[StackFrame, ...]]], None]) -> None:
        """
        查詢一條執行緒的呼叫堆疊，最裡面的一層在最前面
        Ask for a thread's call stack, innermost frame first.

        :param thread_id: 執行緒編號 / the thread's id
        :param on_reply: 收回覆的函式 / receives the reply
        """

    def scopes(self, frame_id: int, on_reply: Callable[[DebugReply[tuple[Scope, ...]]], None]) -> None:
        """
        查詢一層堆疊裡有哪幾組變數
        Ask which groups of variables a frame has.

        :param frame_id: 堆疊那一層的編號 / the frame's id
        :param on_reply: 收回覆的函式 / receives the reply
        """

    def variables(self, reference: int,
                  on_reply: Callable[[DebugReply[tuple[Variable, ...]]], None]) -> None:
        """
        查詢一組變數，或一個變數的子項目
        Ask for a group of variables, or for a variable's children.

        :param reference: :class:`Scope` 或 :class:`Variable` 給的編號
            the handle a :class:`Scope` or a :class:`Variable` gave
        :param on_reply: 收回覆的函式 / receives the reply
        """

    def evaluate(self, expression: str, frame_id: int,
                 on_reply: Callable[[DebugReply[EvaluateResult | None]], None]) -> None:
        """
        在某一層堆疊裡求一個運算式的值
        Evaluate an expression in a frame.

        :param expression: 運算式 / the expression
        :param frame_id: 堆疊那一層的編號，零表示全域 / the frame's id, zero for the global scope
        :param on_reply: 收回覆的函式 / receives the reply
        """

    def exception_info(self, thread_id: int,
                       on_reply: Callable[[DebugReply[ExceptionInfo | None]], None]) -> None:
        """
        查詢一條執行緒停在哪個例外上
        Ask which exception a thread stopped on.

        :param thread_id: 執行緒編號 / the thread's id
        :param on_reply: 收回覆的函式 / receives the reply
        """

    def terminate(self) -> None:
        """
        結束除錯並放掉它持有的程序
        End the run and release the process it holds.
        """


# 建立一個新的除錯工作階段 / Builds one new debug session
DebugSessionFactory = Callable[[], DebugSession]

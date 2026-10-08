"""
視窗這一端的除錯控制：把除錯工作階段接到 Qt
Debugging as the window sees it: a debug session connected to Qt.

除錯工作階段在自己的執行緒上回覆與通知；畫面只能在畫面執行緒上更新。這個類別
站在中間：它訂閱工作階段的事件、把查詢的回覆變成 Qt 訊號，訊號跨執行緒時 Qt 會
自動排進畫面執行緒。面板與編輯器只認這個類別，不認工作階段背後是哪個轉接器。
A debug session replies and announces on a thread of its own, and widgets may
only be touched on the widget thread. This class stands between the two: it
subscribes to the session's events and turns replies into Qt signals, which Qt
queues onto the widget thread when they cross threads. The panel and the editor
know this class only, never which adapter is behind the session.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from PySide6.QtCore import QObject, Signal

from je_editor.core.debug.debug_session import (
    Breakpoint, DebugAttachRequest, DebugLaunchRequest, DebugSession, DebugState, StepKind
)
from je_editor.core.services.editor_services import EditorServices
from je_editor.utils.exception.exceptions import JEditorServiceException
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 預設使用的轉接器 / The adapter used unless told otherwise
DEFAULT_ADAPTER = "debugpy"
_ACTIVE_STATES = (DebugState.STARTING, DebugState.RUNNING, DebugState.PAUSED)
# 這一類輸出是轉接器給工具看的，不是給人看的 / Output of this kind is for tools, not for people
_HIDDEN_OUTPUT = "telemetry"


class DebugController(QObject):
    """
    一個視窗的除錯控制
    The debugging control of one window.
    """

    state_changed = Signal(object)        # DebugState
    stopped = Signal(object)              # StopEvent
    output = Signal(str, str)             # 類別與文字 / category and text
    threads_ready = Signal(object)        # tuple[DebugThread, ...]
    stack_ready = Signal(int, object)     # 執行緒編號與堆疊 / thread id and frames
    scopes_ready = Signal(int, object)    # 堆疊層編號與變數群組 / frame id and scopes
    variables_ready = Signal(int, object)  # 編號與變數 / reference and variables
    evaluated = Signal(str, object)       # 運算式與 DebugReply / expression and its DebugReply
    exception_ready = Signal(object)      # ExceptionInfo | None

    def __init__(self, services: EditorServices, parent: QObject | None = None,
                 adapter: str = DEFAULT_ADAPTER) -> None:
        """
        :param services: 視窗的核心服務，除錯轉接器登記在裡面
            the window's core services, where debug adapters are registered
        :param parent: Qt 父物件 / the Qt parent
        :param adapter: 要用哪個轉接器 / which adapter to use
        """
        super().__init__(parent)
        self.setObjectName("DebugController")
        self._services = services
        self._adapter = adapter
        self._session: DebugSession | None = None
        self._unsubscribe: list[Callable[[], None]] = []

    def available(self) -> bool:
        """
        這個視窗能不能用除錯轉接器除錯
        Whether this window can debug through a debug adapter.

        :return: 轉接器有登記時為 ``True`` / ``True`` when the adapter is registered
        """
        return self._adapter in self._services.debug_adapters.names()

    def state(self) -> DebugState:
        """
        目前的除錯狀態
        The current debugging state.

        :return: 狀態；沒有除錯過時為 ``IDLE`` / the state, ``IDLE`` before any debugging
        """
        return DebugState.IDLE if self._session is None else self._session.state()

    def is_active(self) -> bool:
        """
        是否正在除錯
        Whether a program is being debugged right now.

        :return: 啟動中、執行中或暫停時為 ``True`` / ``True`` while starting, running or paused
        """
        return self.state() in _ACTIVE_STATES

    def launch(self, request: DebugLaunchRequest,
               breakpoints: Mapping[str, Sequence[Breakpoint]]) -> bool:
        """
        啟動程式並開始除錯
        Launch a program under the debugger.

        :param request: 啟動所需的資訊 / what to launch
        :param breakpoints: 每個檔案（URI）的中斷點 / the breakpoints of each file, by URI
        :return: 有啟動時為 ``True`` / ``True`` when it started
        """
        session = self._new_session(breakpoints)
        return session is not None and session.launch(request)

    def attach(self, request: DebugAttachRequest,
               breakpoints: Mapping[str, Sequence[Breakpoint]]) -> bool:
        """
        接上一個已經在等除錯器的程式
        Attach to a program that is already waiting for a debugger.

        :param request: 要接上哪裡 / where to attach
        :param breakpoints: 每個檔案（URI）的中斷點 / the breakpoints of each file, by URI
        :return: 有連上時為 ``True`` / ``True`` when it connected
        """
        session = self._new_session(breakpoints)
        return session is not None and session.attach(request)

    def set_breakpoints(self, uri: str, breakpoints: Sequence[Breakpoint]) -> None:
        """
        除錯中途更新一個檔案的中斷點
        Update one file's breakpoints while debugging.

        :param uri: 檔案的 URI / the file's URI
        :param breakpoints: 這個檔案現在所有的中斷點 / all its breakpoints now
        """
        if self._session is not None and self.is_active():
            self._session.set_breakpoints(uri, breakpoints)

    def resume(self) -> None:
        """繼續執行 / Carry on running."""
        if self._session is not None and self.state() is DebugState.PAUSED:
            self._session.resume()

    def pause(self) -> None:
        """暫停執行 / Pause the run."""
        if self._session is not None and self.state() is DebugState.RUNNING:
            self._session.pause()

    def step(self, kind: StepKind) -> bool:
        """
        逐步執行
        Take one step.

        :param kind: 逐步的方式 / how to step
        :return: 有送出時為 ``True``；沒有暫停中的程式時為 ``False``
            ``True`` when it was sent, ``False`` when no program is paused
        """
        if self._session is None or self.state() is not DebugState.PAUSED:
            return False
        self._session.step(kind)
        return True

    def stop(self) -> None:
        """結束除錯 / End the debugging."""
        if self._session is not None:
            self._session.terminate()

    def request_threads(self) -> None:
        """查詢執行緒，結果由 ``threads_ready`` 送出 / Ask for the threads; ``threads_ready`` carries them."""
        if self._session is not None:
            self._session.threads(lambda reply: self.threads_ready.emit(reply.value))

    def request_stack(self, thread_id: int) -> None:
        """
        查詢一條執行緒的堆疊，結果由 ``stack_ready`` 送出
        Ask for a thread's stack; ``stack_ready`` carries it.

        :param thread_id: 執行緒編號 / the thread's id
        """
        if self._session is not None:
            self._session.stack_trace(
                thread_id, lambda reply: self.stack_ready.emit(thread_id, reply.value))

    def request_scopes(self, frame_id: int) -> None:
        """
        查詢一層堆疊的變數群組，結果由 ``scopes_ready`` 送出
        Ask for a frame's scopes; ``scopes_ready`` carries them.

        :param frame_id: 堆疊那一層的編號 / the frame's id
        """
        if self._session is not None:
            self._session.scopes(frame_id, lambda reply: self.scopes_ready.emit(frame_id, reply.value))

    def request_variables(self, reference: int) -> None:
        """
        查詢一組變數或一個變數的子項目，結果由 ``variables_ready`` 送出
        Ask for a group of variables or a variable's children; ``variables_ready`` carries them.

        :param reference: 變數群組或變數給的編號 / the handle a scope or a variable gave
        """
        if self._session is not None:
            self._session.variables(
                reference, lambda reply: self.variables_ready.emit(reference, reply.value))

    def evaluate(self, expression: str, frame_id: int) -> None:
        """
        求一個運算式的值，結果由 ``evaluated`` 送出
        Evaluate an expression; ``evaluated`` carries the result.

        :param expression: 運算式 / the expression
        :param frame_id: 堆疊那一層的編號，零表示全域 / the frame's id, zero for the global scope
        """
        if self._session is not None:
            self._session.evaluate(
                expression, frame_id, lambda reply: self.evaluated.emit(expression, reply))

    def request_exception(self, thread_id: int) -> None:
        """
        查詢一條執行緒停在哪個例外上，結果由 ``exception_ready`` 送出
        Ask which exception a thread stopped on; ``exception_ready`` carries it.

        :param thread_id: 執行緒編號 / the thread's id
        """
        if self._session is not None:
            self._session.exception_info(thread_id, lambda reply: self.exception_ready.emit(reply.value))

    def _new_session(self, breakpoints: Mapping[str, Sequence[Breakpoint]]) -> DebugSession | None:
        """建立新的工作階段、訂閱它的事件並交給它中斷點 / Build a session, subscribe to it and hand it the breakpoints."""
        if self.is_active():
            return None
        try:
            session = self._services.debug_adapters.require(self._adapter)()
        except JEditorServiceException as error:
            jeditor_logger.warning("no debug adapter to start: %s", error)
            return None
        for unsubscribe in self._unsubscribe:
            unsubscribe()
        self._session = session
        self._unsubscribe = [
            session.state_changed.subscribe(self.state_changed.emit),
            session.stopped.subscribe(self.stopped.emit),
            session.output.subscribe(self._on_output),
        ]
        for uri, items in breakpoints.items():
            session.set_breakpoints(uri, items)
        return session

    def _on_output(self, event) -> None:
        """把給人看的輸出送出去 / Pass on the output meant for people."""
        if event.category != _HIDDEN_OUTPUT:
            self.output.emit(event.category, event.text)

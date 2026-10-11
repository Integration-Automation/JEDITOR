"""
透過 Debug Adapter Protocol 跟除錯轉接器對話的除錯工作階段
A debug session that talks to a debug adapter over the Debug Adapter Protocol.

轉接器是一個子程序，以標準輸入與標準輸出收發 DAP 訊息。這個類別負責啟動它、照
協定規定的順序打招呼（``initialize`` → ``launch`` 或 ``attach`` → 等 ``initialized``
事件 → 送出中斷點 → ``configurationDone``），再把之後的事件與回應轉成核心層的
資料物件。它不知道被除錯的是哪一種語言：轉接器的指令與啟動引數都由外面給。
The adapter is a child process that exchanges DAP messages over its standard
input and output. This class starts it, greets it in the order the protocol
demands (``initialize``, then ``launch`` or ``attach``, then wait for the
``initialized`` event, send the breakpoints, ``configurationDone``), and turns
the events and responses that follow into the core layer's data objects. It
does not know which language is being debugged: the adapter's command and the
launch arguments are given from outside.

回應與事件都在讀取轉接器輸出的那條執行緒上處理，訂閱者與收回覆的函式也在那條
執行緒上被呼叫。
Responses and events are handled on the thread that reads the adapter's output,
and subscribers and reply functions are called on that thread too.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Sequence

from je_editor.core.debug.debug_session import (
    Breakpoint, BreakpointStatus, DebugAttachRequest, DebugLaunchRequest, DebugReply, DebugState,
    DebugThread, EvaluateResult, ExceptionInfo, OutputEvent, Scope, StackFrame, StepKind,
    StopEvent, Variable
)
from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import OutputStream, TaskHandle, TaskRunner, TaskSpec
from je_editor.core.uri.resource_uri import to_path, to_uri
from je_editor.utils.dap.dap_protocol import (
    TYPE_EVENT, TYPE_RESPONSE, MessageReader, encode_message, items_of, message_kind, number_of,
    request, source_breakpoints, text_of
)
from je_editor.utils.logging.loggin_instance import jeditor_logger

ResponseHandler = Callable[[dict], None]
# 送出 disconnect 之後等轉接器自己結束的秒數，超過就直接結束它
# Seconds to wait for the adapter to exit by itself after disconnect, before it is stopped
DISCONNECT_GRACE_SECONDS = 3.0
# 一次最多要幾層堆疊 / The most stack frames asked for at once
MAX_STACK_FRAMES = 200
_STEP_COMMANDS = {StepKind.OVER: "next", StepKind.INTO: "stepIn", StepKind.OUT: "stepOut"}
_CONSOLE = "console"


def _nothing(_response: dict) -> None:
    """不需要看回應的請求用這個 / For requests whose response nobody needs."""


class DapSession:
    """
    以 DAP 轉接器實作的除錯工作階段
    The debug session implemented with a DAP adapter.
    """

    def __init__(self, adapter_command: Sequence[str], runner: TaskRunner, adapter_id: str,
                 launch_arguments: Callable[[DebugLaunchRequest], dict],
                 attach_arguments: Callable[[DebugAttachRequest], dict],
                 attach_channel: Callable[[DebugAttachRequest], TaskHandle] | None = None) -> None:
        """
        :param adapter_command: 啟動轉接器的指令 / the command that starts the adapter
        :param runner: 用來啟動轉接器的地方；換成遠端的就是遠端除錯
            where the adapter is started; a remote one makes this remote debugging
        :param adapter_id: 轉接器的名稱，會放進 ``initialize`` / the adapter's name, sent in ``initialize``
        :param launch_arguments: 把啟動請求變成這個轉接器的 ``launch`` 引數
            turns a launch request into this adapter's ``launch`` arguments
        :param attach_arguments: 把連線請求變成這個轉接器的 ``attach`` 引數
            turns an attach request into this adapter's ``attach`` arguments
        :param attach_channel: 接上既有程式時要用哪條通道講協定；沒給時跟啟動一樣，
            另開一個轉接器程序。對方自己帶著轉接器等連線的（例如 debugpy）要給這個
            the channel the protocol is spoken over when attaching; when omitted
            an adapter process is started as for a launch. Needed where the other
            side waits with an adapter of its own, as debugpy does
        """
        self._adapter_command = tuple(adapter_command)
        self._runner = runner
        self._adapter_id = adapter_id
        self._launch_arguments = launch_arguments
        self._attach_arguments = attach_arguments
        self._attach_channel = attach_channel
        self._state_changed = EventHook()
        self._stopped = EventHook()
        self._output = EventHook()
        self._breakpoints_reported = EventHook()
        self._state = DebugState.IDLE
        self._task: TaskHandle | None = None
        self._reader = MessageReader()
        self._lock = threading.Lock()
        self._seq = 0
        self._pending: dict[int, ResponseHandler] = {}
        self._breakpoints: dict[str, tuple[Breakpoint, ...]] = {}
        self._configured = False
        self._stopped_thread = 0

    @property
    def state_changed(self) -> EventHook:
        """狀態改變後發出，引數是新的狀態 / Fired with the new state."""
        return self._state_changed

    @property
    def stopped(self) -> EventHook:
        """程式停下來時發出，引數是 ``StopEvent`` / Fired with a ``StopEvent`` when the program stops."""
        return self._stopped

    @property
    def output(self) -> EventHook:
        """有輸出時發出，引數是 ``OutputEvent`` / Fired with an ``OutputEvent``."""
        return self._output

    @property
    def breakpoints_reported(self) -> EventHook:
        """轉接器回報中斷點時發出，引數是一組 ``BreakpointStatus`` / Fired with the reported breakpoints."""
        return self._breakpoints_reported

    def state(self) -> DebugState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """
        return self._state

    def launch(self, request_: DebugLaunchRequest) -> bool:
        """
        啟動程式並開始除錯
        Launch the program under the debugger.

        :param request_: 啟動所需的資訊 / what to launch
        :return: 轉接器有啟動時為 ``True`` / ``True`` when the adapter started
        """
        return self._begin("launch", self._launch_arguments(request_), self._adapter_process())

    def attach(self, request_: DebugAttachRequest) -> bool:
        """
        接上一個已經在執行的程式
        Attach to a program that is already running.

        :param request_: 要接上哪裡 / where to attach
        :return: 有連上轉接器時為 ``True`` / ``True`` when the adapter was reached
        """
        channel = (self._adapter_process() if self._attach_channel is None
                   else self._attach_channel(request_))
        return self._begin("attach", self._attach_arguments(request_), channel)

    def set_breakpoints(self, uri: str, breakpoints: Sequence[Breakpoint]) -> None:
        """
        設定某個資源的全部中斷點
        Set every breakpoint of one resource.

        還沒啟動時先記著，轉接器準備好之後一起送出。
        Before the launch they are kept, and sent once the adapter is ready.

        :param uri: 資源的 URI / the resource's URI
        :param breakpoints: 這個資源現在所有的中斷點 / all its breakpoints now
        """
        self._breakpoints[uri] = tuple(item for item in breakpoints if item.enabled)
        if self._configured:
            self._send_breakpoints(uri)

    def resume(self, thread_id: int = 0) -> None:
        """
        繼續執行
        Carry on running.

        :param thread_id: 要繼續的執行緒，零表示上次停下來的那一條
            the thread to resume, zero for the one that stopped last
        """
        self._send("continue", {"threadId": thread_id or self._stopped_thread}, _nothing)

    def pause(self, thread_id: int = 0) -> None:
        """
        暫停執行
        Pause the run.

        :param thread_id: 要暫停的執行緒，零表示上次停下來的那一條
            the thread to pause, zero for the one that stopped last
        """
        self._send("pause", {"threadId": thread_id or self._stopped_thread}, _nothing)

    def step(self, kind: StepKind, thread_id: int = 0) -> None:
        """
        逐步執行
        Take one step.

        :param kind: 逐步的方式 / how to step
        :param thread_id: 要逐步的執行緒，零表示上次停下來的那一條
            the thread to step, zero for the one that stopped last
        """
        self._send(_STEP_COMMANDS[kind], {"threadId": thread_id or self._stopped_thread}, _nothing)

    def threads(self, on_reply: Callable[[DebugReply[tuple[DebugThread, ...]]], None]) -> None:
        """
        查詢程式裡的執行緒
        Ask for the program's threads.

        :param on_reply: 收回覆的函式 / receives the reply
        """
        self._query("threads", {}, on_reply, (), lambda body: tuple(
            DebugThread(number_of(item, "id"), text_of(item, "name"))
            for item in items_of(body, "threads")))

    def stack_trace(self, thread_id: int,
                    on_reply: Callable[[DebugReply[tuple[StackFrame, ...]]], None]) -> None:
        """
        查詢一條執行緒的呼叫堆疊，最裡面的一層在最前面
        Ask for a thread's call stack, innermost frame first.

        :param thread_id: 執行緒編號 / the thread's id
        :param on_reply: 收回覆的函式 / receives the reply
        """
        arguments = {"threadId": thread_id, "startFrame": 0, "levels": MAX_STACK_FRAMES}
        self._query("stackTrace", arguments, on_reply, (), lambda body: tuple(
            _frame(item) for item in items_of(body, "stackFrames")))

    def scopes(self, frame_id: int, on_reply: Callable[[DebugReply[tuple[Scope, ...]]], None]) -> None:
        """
        查詢一層堆疊裡有哪幾組變數
        Ask which groups of variables a frame has.

        :param frame_id: 堆疊那一層的編號 / the frame's id
        :param on_reply: 收回覆的函式 / receives the reply
        """
        self._query("scopes", {"frameId": frame_id}, on_reply, (), lambda body: tuple(
            Scope(text_of(item, "name"), number_of(item, "variablesReference"),
                  item.get("expensive") is True)
            for item in items_of(body, "scopes")))

    def variables(self, reference: int,
                  on_reply: Callable[[DebugReply[tuple[Variable, ...]]], None]) -> None:
        """
        查詢一組變數，或一個變數的子項目
        Ask for a group of variables, or for a variable's children.

        :param reference: ``Scope`` 或 ``Variable`` 給的編號 / the handle a scope or a variable gave
        :param on_reply: 收回覆的函式 / receives the reply
        """
        self._query("variables", {"variablesReference": reference}, on_reply, (), lambda body: tuple(
            Variable(text_of(item, "name"), text_of(item, "value"), text_of(item, "type"),
                     number_of(item, "variablesReference"))
            for item in items_of(body, "variables")))

    def evaluate(self, expression: str, frame_id: int,
                 on_reply: Callable[[DebugReply[EvaluateResult | None]], None]) -> None:
        """
        在某一層堆疊裡求一個運算式的值
        Evaluate an expression in a frame.

        :param expression: 運算式 / the expression
        :param frame_id: 堆疊那一層的編號，零表示全域 / the frame's id, zero for the global scope
        :param on_reply: 收回覆的函式 / receives the reply
        """
        arguments: dict = {"expression": expression, "context": "repl"}
        if frame_id:
            arguments["frameId"] = frame_id
        self._query("evaluate", arguments, on_reply, None, lambda body: EvaluateResult(
            text_of(body, "result"), text_of(body, "type"), number_of(body, "variablesReference")))

    def exception_info(self, thread_id: int,
                       on_reply: Callable[[DebugReply[ExceptionInfo | None]], None]) -> None:
        """
        查詢一條執行緒停在哪個例外上
        Ask which exception a thread stopped on.

        :param thread_id: 執行緒編號 / the thread's id
        :param on_reply: 收回覆的函式 / receives the reply
        """
        self._query("exceptionInfo", {"threadId": thread_id}, on_reply, None, lambda body: ExceptionInfo(
            text_of(body, "exceptionId"), text_of(body, "description"), text_of(body, "breakMode"),
            text_of(body.get("details"), "stackTrace")))

    def terminate(self) -> None:
        """
        結束除錯並放掉它持有的程序
        End the run and release the process it holds.

        先請轉接器結束被除錯的程式；它沒有在期限內自己結束的話，就直接結束它。
        The adapter is asked to end the program being debugged first, and is
        stopped outright when it has not exited by itself in time.
        """
        task = self._task
        if task is None or self._state in (DebugState.IDLE, DebugState.TERMINATED):
            return
        self._send("disconnect", {"terminateDebuggee": True}, _nothing)
        timer = threading.Timer(DISCONNECT_GRACE_SECONDS, task.cancel)
        timer.daemon = True
        timer.start()

    def _adapter_process(self) -> TaskHandle:
        """準備一個轉接器程序，還不啟動 / Prepare an adapter process without starting it."""
        return self._runner.create(TaskSpec(self._adapter_command, name="debug adapter", binary=True))

    def _begin(self, command: str, arguments: dict, task: TaskHandle) -> bool:
        """接上轉接器並開始打招呼 / Reach the adapter and begin the handshake."""
        if self._state not in (DebugState.IDLE, DebugState.TERMINATED):
            return False
        self._reader = MessageReader()
        self._configured = False
        self._stopped_thread = 0
        task.output.subscribe(self._on_adapter_output)
        task.finished.subscribe(self._on_adapter_finished)
        self._task = task
        if not task.start():
            self._task = None
            return False
        self._set_state(DebugState.STARTING)
        self._send("initialize", {
            "clientID": "jeditor", "clientName": "JEditor", "adapterID": self._adapter_id,
            "linesStartAt1": True, "columnsStartAt1": True, "pathFormat": "path",
            "supportsVariableType": True, "supportsRunInTerminalRequest": False,
        }, lambda _response: self._send(command, arguments, self._on_started))
        return True

    def _on_started(self, response: dict) -> None:
        """``launch`` 或 ``attach`` 的回應 / The response to ``launch`` or ``attach``."""
        if response.get("success") is not True:
            self._output.emit(OutputEvent(_CONSOLE, text_of(response, "message", "the debugger could not start")))
            self.terminate()
        elif self._state is DebugState.STARTING:
            self._set_state(DebugState.RUNNING)

    def _configure(self) -> None:
        """轉接器準備好了：送出記著的中斷點，再宣告設定完成 / The adapter is ready: send the breakpoints, then finish configuring."""
        self._configured = True
        for uri in list(self._breakpoints):
            self._send_breakpoints(uri)
        self._send("setExceptionBreakpoints", {"filters": ["uncaught"]}, _nothing)
        self._send("configurationDone", {}, _nothing)

    def _send_breakpoints(self, uri: str) -> None:
        """把一個資源的中斷點送給轉接器 / Send one resource's breakpoints to the adapter."""
        wanted = self._breakpoints.get(uri, ())
        arguments = {
            "source": {"path": to_path(uri)},
            "breakpoints": source_breakpoints([(item.line, item.condition) for item in wanted]),
        }

        def report(response: dict) -> None:
            statuses = tuple(
                BreakpointStatus(uri, number_of(item, "line"), item.get("verified") is True,
                                 text_of(item, "message"))
                for item in items_of(response.get("body"), "breakpoints"))
            self._breakpoints_reported.emit(statuses)

        self._send("setBreakpoints", arguments, report)

    def _query(self, command: str, arguments: dict, on_reply: Callable, empty: object,
               parse: Callable[[dict], object]) -> None:
        """送出一個查詢，把回應變成 ``DebugReply`` / Send a query and turn its response into a ``DebugReply``."""

        def respond(response: dict) -> None:
            body = response.get("body")
            if response.get("success") is True and isinstance(body, dict):
                on_reply(DebugReply(parse(body)))
            else:
                on_reply(DebugReply(empty, text_of(response, "message", f"{command} failed")))

        if not self._send(command, arguments, respond):
            on_reply(DebugReply(empty, "the debugger is not running"))

    def _send(self, command: str, arguments: dict, on_response: ResponseHandler) -> bool:
        """送出一個請求，並記下誰要它的回應 / Send a request and remember who wants its response."""
        task = self._task
        if task is None:
            return False
        with self._lock:
            self._seq += 1
            seq = self._seq
            self._pending[seq] = on_response
        if task.write(encode_message(request(seq, command, arguments))):
            return True
        with self._lock:
            self._pending.pop(seq, None)
        return False

    def _on_adapter_output(self, stream: OutputStream, data: bytes) -> None:
        """轉接器寫了東西：標準輸出是協定訊息，標準錯誤是給人看的 / The adapter wrote: protocol on stdout, text for people on stderr."""
        if stream is OutputStream.STDERR:
            self._output.emit(OutputEvent(_CONSOLE, data.decode("utf-8", "replace")))
            return
        for message in self._reader.feed(data):
            kind = message_kind(message)
            if kind == TYPE_RESPONSE:
                self._on_response(message)
            elif kind == TYPE_EVENT:
                self._on_event(text_of(message, "event"), message.get("body"))

    def _on_response(self, message: dict) -> None:
        """把回應交給當初送出請求的人 / Hand a response to whoever sent the request."""
        with self._lock:
            handler = self._pending.pop(number_of(message, "request_seq"), None)
        if handler is not None:
            handler(message)

    def _on_event(self, event: str, body: object) -> None:
        """處理轉接器送來的事件 / Handle an event from the adapter."""
        if event == "initialized":
            self._configure()
        elif event == "stopped":
            self._stopped_thread = number_of(body, "threadId")
            self._set_state(DebugState.PAUSED)
            all_stopped = not isinstance(body, dict) or body.get("allThreadsStopped") is not False
            self._stopped.emit(StopEvent(text_of(body, "reason"), self._stopped_thread,
                                         text_of(body, "description"), text_of(body, "text"), all_stopped))
        elif event == "continued":
            self._set_state(DebugState.RUNNING)
        elif event == "output":
            self._output.emit(OutputEvent(text_of(body, "category", _CONSOLE), text_of(body, "output")))
        elif event == "terminated":
            self.terminate()

    def _on_adapter_finished(self, exit_code: int) -> None:
        """轉接器結束了：沒等到回應的請求都算失敗 / The adapter ended: every request still waiting has failed."""
        jeditor_logger.info("debug adapter %s exited with %s", self._adapter_id, exit_code)
        with self._lock:
            waiting, self._pending = list(self._pending.values()), {}
        self._task = None
        self._configured = False
        for handler in waiting:
            handler({"success": False, "message": "the debugger has ended"})
        self._set_state(DebugState.TERMINATED)

    def _set_state(self, state: DebugState) -> None:
        """換狀態，真的變了才通知 / Change state, announcing it only when it really changed."""
        if state is not self._state:
            self._state = state
            self._state_changed.emit(state)


def _frame(item: dict) -> StackFrame:
    """把 DAP 的一層堆疊變成 ``StackFrame`` / Turn one DAP stack frame into a ``StackFrame``."""
    path = text_of(item.get("source"), "path")
    return StackFrame(number_of(item, "id"), text_of(item, "name"), to_uri(path) if path else "",
                      number_of(item, "line", 1), number_of(item, "column", 1))

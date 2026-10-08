"""Tests for the DAP messages, the local task runner and the DAP debug session against a scripted adapter."""
from __future__ import annotations

import socket
import sys
import threading

import pytest

from je_editor.adapters.debug import debugpy_adapter
from je_editor.adapters.debug.dap_session import MAX_STACK_FRAMES, DapSession
from je_editor.adapters.debug.socket_channel import SocketChannel
from je_editor.adapters.default_services import LOCAL_RUNNER, build_default_services
from je_editor.adapters.process.local_task_runner import LocalTask, LocalTaskRunner
from je_editor.core.debug.debug_session import (
    Breakpoint, BreakpointStatus, DebugAttachRequest, DebugLaunchRequest, DebugReply, DebugSession,
    DebugState, DebugThread, EvaluateResult, ExceptionInfo, OutputEvent, Scope, StackFrame,
    StepKind, StopEvent, Variable
)
from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import (
    OutputStream, TaskHandle, TaskRunner, TaskSpec, TaskState
)
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.core.uri.resource_uri import to_path, to_uri
from je_editor.utils.dap.dap_protocol import (
    MessageReader, encode_message, items_of, message_kind, number_of, request, source_breakpoints,
    text_of
)
from je_editor.utils.exception.exceptions import JEditorServiceException

WAIT_SECONDS = 20


class TestMessages:
    def test_a_request_carries_its_number_command_and_arguments(self):
        assert request(3, "stackTrace", {"threadId": 1}) == {
            "seq": 3, "type": "request", "command": "stackTrace", "arguments": {"threadId": 1}}

    def test_a_request_without_arguments_has_no_arguments_field(self):
        assert request(1, "threads") == {"seq": 1, "type": "request", "command": "threads"}

    def test_a_message_survives_framing(self):
        reader = MessageReader()
        frames = encode_message(request(1, "threads")) + encode_message(request(2, "pause"))
        assert [message["seq"] for message in reader.feed(frames[:30]) + reader.feed(frames[30:])] == [1, 2]

    @pytest.mark.parametrize("message, kind", [
        ({"type": "response"}, "response"), ({"type": "event"}, "event"),
        ({"type": "request"}, "request"), ({"type": "other"}, ""), ({}, ""), ("text", ""), (None, ""),
    ])
    def test_the_kind_of_a_message(self, message, kind):
        assert message_kind(message) == kind

    @pytest.mark.parametrize("source", [None, "text", 7, [], {"name": 5}, {"other": "x"}])
    def test_a_missing_or_wrong_text_field_is_the_default(self, source):
        assert text_of(source, "name", "fallback") == "fallback"

    @pytest.mark.parametrize("source", [None, {"id": "7"}, {"id": 1.5}, {"id": True}, {}])
    def test_a_missing_or_wrong_number_field_is_the_default(self, source):
        assert number_of(source, "id", -1) == -1

    def test_fields_that_are_right_are_read(self):
        assert (text_of({"name": "main"}, "name"), number_of({"id": 7}, "id")) == ("main", 7)

    @pytest.mark.parametrize("source", [None, {"frames": "x"}, {"frames": None}, {}])
    def test_a_missing_or_wrong_list_field_is_empty(self, source):
        assert items_of(source, "frames") == []

    def test_only_mappings_are_kept_from_a_list_field(self):
        assert items_of({"frames": [{"id": 1}, "junk", 3, {"id": 2}]}, "frames") == [{"id": 1}, {"id": 2}]

    def test_breakpoints_carry_a_condition_only_when_there_is_one(self):
        assert source_breakpoints([(3, ""), (9, "x > 1")]) == [
            {"line": 3}, {"line": 9, "condition": "x > 1"}]


def run_python(runner: LocalTaskRunner, code: str, **options) -> tuple[LocalTask, list, list]:
    """Start ``python -c code`` and collect what it writes and its exit code."""
    task = runner.create(TaskSpec((sys.executable, "-c", code), **options))
    written: list = []
    codes: list = []
    task.output.subscribe(lambda stream, data: written.append((stream, data)))
    task.finished.subscribe(codes.append)
    return task, written, codes


@pytest.fixture()
def runner():
    local = LocalTaskRunner()
    yield local
    local.shutdown()


class TestTheLocalTaskRunner:
    def test_it_satisfies_the_interfaces(self, runner):
        task = runner.create(TaskSpec((sys.executable, "-c", "pass")))
        assert isinstance(runner, TaskRunner) and isinstance(task, TaskHandle)
        assert (task.state(), task.exit_code()) == (TaskState.PENDING, None)

    def test_output_and_the_exit_code_are_reported(self, runner):
        task, written, codes = run_python(runner, "print('hello')")
        assert task.start() is True
        assert task.wait(WAIT_SECONDS)
        text = "".join(data for stream, data in written if stream is OutputStream.STDOUT)
        assert text.strip() == "hello"
        assert (task.state(), task.exit_code()) == (TaskState.FINISHED, 0)
        assert codes == [0]

    def test_standard_error_is_told_apart(self, runner):
        task, written, _codes = run_python(runner, "import sys; sys.stderr.write('oops'); sys.exit(3)")
        task.start()
        task.wait(WAIT_SECONDS)
        assert "".join(data for stream, data in written if stream is OutputStream.STDERR) == "oops"
        assert task.exit_code() == 3

    def test_a_binary_task_delivers_bytes_and_takes_bytes(self, runner):
        code = "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read(3)[::-1]); sys.stdout.flush()"
        task, written, _codes = run_python(runner, code, binary=True)
        task.start()
        assert task.write(b"\x00\x01\xff") is True
        task.wait(WAIT_SECONDS)
        assert b"".join(data for _stream, data in written) == b"\xff\x01\x00"

    def test_text_can_be_written_to_its_input(self, runner):
        task, written, _codes = run_python(runner, "print(input().upper())")
        task.start()
        assert task.write("quiet\n") is True
        task.wait(WAIT_SECONDS)
        assert "".join(data for _stream, data in written).strip() == "QUIET"

    def test_a_program_that_does_not_exist_fails_to_start(self, runner, tmp_path):
        task = runner.create(TaskSpec((str(tmp_path / "no-such-program"),)))
        assert task.start() is False
        assert task.state() is TaskState.FAILED_TO_START
        assert task.write("x") is False

    def test_it_starts_only_once(self, runner):
        task, _written, _codes = run_python(runner, "pass")
        assert (task.start(), task.start()) == (True, False)
        task.wait(WAIT_SECONDS)

    def test_a_running_task_can_be_cancelled(self, runner):
        task, _written, codes = run_python(runner, "import time; time.sleep(120)")
        task.start()
        task.cancel()
        assert task.wait(WAIT_SECONDS)
        assert task.state() is TaskState.CANCELLED
        assert len(codes) == 1

    def test_writing_after_the_end_is_refused(self, runner):
        task, _written, _codes = run_python(runner, "pass")
        task.start()
        task.wait(WAIT_SECONDS)
        assert task.write("late\n") is False

    def test_the_working_directory_and_environment_are_passed_on(self, runner, tmp_path):
        code = "import os; print(os.getcwd()); print(os.environ['JEDITOR_TASK_PROBE'])"
        task, written, _codes = run_python(runner, code, working_directory=str(tmp_path),
                                           environment={"JEDITOR_TASK_PROBE": "seen"})
        task.start()
        task.wait(WAIT_SECONDS)
        lines = "".join(data for _stream, data in written).split()
        assert (to_path(to_uri(lines[0])), lines[1]) == (to_path(to_uri(str(tmp_path))), "seen")

    def test_shutting_the_runner_down_stops_what_is_running(self, runner):
        task, _written, _codes = run_python(runner, "import time; time.sleep(120)")
        task.start()
        runner.shutdown()
        assert task.wait(WAIT_SECONDS)
        assert task.state() is TaskState.CANCELLED

    def test_cancelling_before_the_start_or_after_the_end_does_nothing(self, runner):
        task, _written, _codes = run_python(runner, "pass")
        task.cancel()
        task.start()
        task.wait(WAIT_SECONDS)
        task.cancel()
        assert task.state() is TaskState.FINISHED


class ScriptedAdapter:
    """Stands in for the adapter process: records what is sent to it and says what the test tells it to."""

    def __init__(self, starts: bool = True) -> None:
        self.spec: TaskSpec | None = None
        self.output = EventHook()
        self.finished = EventHook()
        self.sent: list[dict] = []
        self.cancelled = 0
        self._starts = starts
        self._alive = False
        self._reader = MessageReader()

    def create(self, spec: TaskSpec) -> ScriptedAdapter:
        self.spec = spec
        return self

    def shutdown(self) -> None:
        self.cancel()

    def state(self) -> TaskState:
        return TaskState.RUNNING if self._alive else TaskState.PENDING

    def exit_code(self) -> int | None:
        return None

    def start(self) -> bool:
        self._alive = self._starts
        return self._starts

    def write(self, data) -> bool:
        if not self._alive:
            return False
        self.sent.extend(self._reader.feed(data))
        return True

    def cancel(self) -> None:
        self.cancelled += 1

    def commands(self) -> list[str]:
        return [message["command"] for message in self.sent]

    def last(self, command: str) -> dict:
        return [message for message in self.sent if message["command"] == command][-1]

    def says(self, message: dict) -> None:
        self.output.emit(OutputStream.STDOUT, encode_message(message))

    def answers(self, command: str, body: dict | None = None, success: bool = True,
                message: str = "") -> None:
        reply = {"type": "response", "request_seq": self.last(command)["seq"], "command": command,
                 "success": success}
        if body is not None:
            reply["body"] = body
        if message:
            reply["message"] = message
        self.says(reply)

    def event(self, name: str, body: dict | None = None) -> None:
        self.says({"type": "event", "event": name, "body": body or {}})

    def exits(self, code: int = 0) -> None:
        self._alive = False
        self.finished.emit(code)


def session_with(adapter: ScriptedAdapter) -> DapSession:
    return DapSession(("adapter",), adapter, "scripted",
                      lambda launch: {"program": launch.program},
                      lambda attach: {"port": attach.port})


@pytest.fixture()
def adapter():
    return ScriptedAdapter()


@pytest.fixture()
def session(adapter):
    return session_with(adapter)


@pytest.fixture()
def running(adapter, session):
    """A session taken through the whole handshake, with the program running."""
    session.launch(DebugLaunchRequest("main.py"))
    adapter.answers("initialize", {})
    adapter.event("initialized")
    adapter.answers("launch")
    return session


@pytest.fixture()
def paused(adapter, running):
    adapter.event("stopped", {"reason": "breakpoint", "threadId": 7, "allThreadsStopped": True})
    return running


def replies_to(ask) -> list[DebugReply]:
    collected: list[DebugReply] = []
    ask(collected.append)
    return collected


class TestTheHandshake:
    def test_the_session_satisfies_the_interface(self, session):
        assert isinstance(session, DebugSession)
        assert session.state() is DebugState.IDLE

    def test_the_adapter_is_started_as_a_binary_task(self, adapter, session):
        assert session.launch(DebugLaunchRequest("main.py")) is True
        assert (adapter.spec.command, adapter.spec.binary) == (("adapter",), True)
        assert session.state() is DebugState.STARTING

    def test_initialize_comes_first_and_launch_only_after_its_answer(self, adapter, session):
        session.launch(DebugLaunchRequest("main.py"))
        assert adapter.commands() == ["initialize"]
        assert adapter.last("initialize")["arguments"]["linesStartAt1"] is True
        adapter.answers("initialize", {})
        assert adapter.commands() == ["initialize", "launch"]
        assert adapter.last("launch")["arguments"] == {"program": "main.py"}

    def test_breakpoints_are_sent_once_the_adapter_says_it_is_ready(self, adapter, session, tmp_path):
        uri = to_uri(tmp_path / "main.py")
        session.set_breakpoints(uri, [Breakpoint(uri, 3), Breakpoint(uri, 9, "x > 1"),
                                      Breakpoint(uri, 12, enabled=False)])
        session.launch(DebugLaunchRequest("main.py"))
        adapter.answers("initialize", {})
        assert "setBreakpoints" not in adapter.commands()
        adapter.event("initialized")
        assert adapter.commands()[2:] == ["setBreakpoints", "setExceptionBreakpoints", "configurationDone"]
        sent = adapter.last("setBreakpoints")["arguments"]
        assert sent["source"]["path"] == to_path(uri)
        assert sent["breakpoints"] == [{"line": 3}, {"line": 9, "condition": "x > 1"}]

    def test_the_program_runs_once_the_launch_is_answered(self, adapter, session):
        states: list[DebugState] = []
        session.state_changed.subscribe(states.append)
        session.launch(DebugLaunchRequest("main.py"))
        adapter.answers("initialize", {})
        adapter.event("initialized")
        adapter.answers("launch")
        assert states == [DebugState.STARTING, DebugState.RUNNING]

    def test_a_second_launch_while_one_is_running_is_refused(self, running):
        assert running.launch(DebugLaunchRequest("other.py")) is False

    def test_an_adapter_that_does_not_start_leaves_the_session_idle(self):
        session = session_with(ScriptedAdapter(starts=False))
        assert session.launch(DebugLaunchRequest("main.py")) is False
        assert session.state() is DebugState.IDLE

    def test_a_refused_launch_is_reported_and_the_adapter_is_told_to_go(self, adapter, session):
        told: list[OutputEvent] = []
        session.output.subscribe(told.append)
        session.launch(DebugLaunchRequest("main.py"))
        adapter.answers("initialize", {})
        adapter.answers("launch", success=False, message="no such file")
        assert told == [OutputEvent("console", "no such file")]
        assert adapter.commands()[-1] == "disconnect"

    def test_attaching_sends_attach(self, adapter, session):
        assert session.attach(DebugAttachRequest(5678)) is True
        adapter.answers("initialize", {})
        assert adapter.last("attach")["arguments"] == {"port": 5678}

    def test_attaching_can_go_over_a_channel_of_the_adapters_choosing(self):
        process, channel = ScriptedAdapter(), ScriptedAdapter()
        asked: list[DebugAttachRequest] = []

        def choose(attach: DebugAttachRequest) -> ScriptedAdapter:
            asked.append(attach)
            return channel

        session = DapSession(("adapter",), process, "scripted", lambda launch: {},
                             lambda attach: {"port": attach.port}, choose)
        assert session.attach(DebugAttachRequest(5678)) is True
        channel.answers("initialize", {})
        assert (channel.commands(), process.sent, asked) == (
            ["initialize", "attach"], [], [DebugAttachRequest(5678)])

    def test_a_channel_that_cannot_connect_leaves_the_session_idle(self):
        session = DapSession(("adapter",), ScriptedAdapter(), "scripted", lambda launch: {},
                             lambda attach: {}, lambda attach: ScriptedAdapter(starts=False))
        assert session.attach(DebugAttachRequest(5678)) is False
        assert session.state() is DebugState.IDLE

    def test_breakpoints_changed_while_running_are_sent_at_once(self, adapter, running, tmp_path):
        uri = to_uri(tmp_path / "late.py")
        running.set_breakpoints(uri, [Breakpoint(uri, 4)])
        assert adapter.last("setBreakpoints")["arguments"]["breakpoints"] == [{"line": 4}]

    def test_what_the_adapter_says_about_breakpoints_is_passed_on(self, adapter, running, tmp_path):
        uri = to_uri(tmp_path / "late.py")
        reported: list[tuple] = []
        running.breakpoints_reported.subscribe(reported.append)
        running.set_breakpoints(uri, [Breakpoint(uri, 4), Breakpoint(uri, 5)])
        adapter.answers("setBreakpoints", {"breakpoints": [
            {"verified": True, "line": 4}, {"verified": False, "line": 6, "message": "no code here"}]})
        assert reported == [(BreakpointStatus(uri, 4, True), BreakpointStatus(uri, 6, False, "no code here"))]


class TestStoppingAndStepping:
    def test_a_stop_pauses_the_session_and_says_why(self, adapter, running):
        stops: list[StopEvent] = []
        running.stopped.subscribe(stops.append)
        adapter.event("stopped", {"reason": "exception", "threadId": 4, "description": "Paused",
                                  "text": "ValueError", "allThreadsStopped": False})
        assert running.state() is DebugState.PAUSED
        assert stops == [StopEvent("exception", 4, "Paused", "ValueError", False)]

    def test_resuming_names_the_thread_that_stopped(self, adapter, paused):
        paused.resume()
        assert adapter.last("continue")["arguments"] == {"threadId": 7}

    def test_a_thread_can_be_named_explicitly(self, adapter, paused):
        paused.pause(3)
        assert adapter.last("pause")["arguments"] == {"threadId": 3}

    @pytest.mark.parametrize("kind, command", [
        (StepKind.OVER, "next"), (StepKind.INTO, "stepIn"), (StepKind.OUT, "stepOut")])
    def test_each_kind_of_step_has_its_command(self, adapter, paused, kind, command):
        paused.step(kind)
        assert adapter.last(command)["arguments"] == {"threadId": 7}

    def test_the_adapter_saying_it_continued_means_running(self, adapter, paused):
        adapter.event("continued", {"threadId": 7})
        assert paused.state() is DebugState.RUNNING

    def test_program_output_is_passed_on_with_its_category(self, adapter, running):
        told: list[OutputEvent] = []
        running.output.subscribe(told.append)
        adapter.event("output", {"category": "stdout", "output": "hello\n"})
        adapter.event("output", {"output": "note"})
        assert told == [OutputEvent("stdout", "hello\n"), OutputEvent("console", "note")]

    def test_what_the_adapter_writes_to_standard_error_is_shown(self, adapter, running):
        told: list[OutputEvent] = []
        running.output.subscribe(told.append)
        adapter.output.emit(OutputStream.STDERR, b"adapter trouble")
        assert told == [OutputEvent("console", "adapter trouble")]

    def test_garbage_from_the_adapter_is_ignored(self, adapter, running):
        adapter.says({"type": "mystery"})
        adapter.says({"type": "response", "request_seq": 9999, "success": True})
        adapter.says({"type": "event", "event": "stopped", "body": "not a mapping"})
        assert running.state() is DebugState.PAUSED


class TestQueries:
    def test_threads(self, adapter, paused):
        replies = replies_to(paused.threads)
        adapter.answers("threads", {"threads": [{"id": 7, "name": "MainThread"}, {"id": 8}]})
        assert replies == [DebugReply((DebugThread(7, "MainThread"), DebugThread(8, "")))]

    def test_the_stack_innermost_first_with_uris(self, adapter, paused, tmp_path):
        path = str(tmp_path / "main.py")
        replies = replies_to(lambda reply: paused.stack_trace(7, reply))
        assert adapter.last("stackTrace")["arguments"] == {
            "threadId": 7, "startFrame": 0, "levels": MAX_STACK_FRAMES}
        adapter.answers("stackTrace", {"stackFrames": [
            {"id": 2, "name": "add", "source": {"path": path}, "line": 3, "column": 5},
            {"id": 1, "name": "<module>"}]})
        assert replies[0].value == (StackFrame(2, "add", to_uri(path), 3, 5),
                                    StackFrame(1, "<module>", "", 1, 1))

    def test_scopes_and_variables(self, adapter, paused):
        scopes = replies_to(lambda reply: paused.scopes(2, reply))
        adapter.answers("scopes", {"scopes": [
            {"name": "Locals", "variablesReference": 5},
            {"name": "Globals", "variablesReference": 6, "expensive": True}]})
        assert scopes[0].value == (Scope("Locals", 5), Scope("Globals", 6, True))
        found = replies_to(lambda reply: paused.variables(5, reply))
        assert adapter.last("variables")["arguments"] == {"variablesReference": 5}
        adapter.answers("variables", {"variables": [
            {"name": "a", "value": "1", "type": "int"},
            {"name": "items", "value": "[1, 2]", "type": "list", "variablesReference": 9}]})
        assert found[0].value == (Variable("a", "1", "int"), Variable("items", "[1, 2]", "list", 9))

    def test_evaluating_in_a_frame_and_globally(self, adapter, paused):
        replies = replies_to(lambda reply: paused.evaluate("a + 1", 2, reply))
        assert adapter.last("evaluate")["arguments"] == {
            "expression": "a + 1", "context": "repl", "frameId": 2}
        adapter.answers("evaluate", {"result": "2", "type": "int"})
        assert replies == [DebugReply(EvaluateResult("2", "int"))]
        paused.evaluate("1", 0, lambda _reply: None)
        assert "frameId" not in adapter.last("evaluate")["arguments"]

    def test_which_exception_stopped_a_thread(self, adapter, paused):
        replies = replies_to(lambda reply: paused.exception_info(7, reply))
        adapter.answers("exceptionInfo", {
            "exceptionId": "ZeroDivisionError", "description": "division by zero",
            "breakMode": "unhandled", "details": {"stackTrace": "Traceback ..."}})
        assert replies == [DebugReply(ExceptionInfo(
            "ZeroDivisionError", "division by zero", "unhandled", "Traceback ..."))]

    def test_a_refused_query_is_an_error_reply_with_the_empty_value(self, adapter, paused):
        frames = replies_to(lambda reply: paused.stack_trace(7, reply))
        adapter.answers("stackTrace", success=False, message="thread is running")
        value = replies_to(lambda reply: paused.evaluate("x", 2, reply))
        adapter.answers("evaluate", success=False)
        assert (frames[0].ok, frames[0].value, frames[0].error) == (False, (), "thread is running")
        assert (value[0].ok, value[0].value, value[0].error) == (False, None, "evaluate failed")

    def test_asking_when_nothing_is_running_answers_at_once(self, session):
        replies = replies_to(session.threads)
        assert (replies[0].ok, replies[0].value) == (False, ())


class TestEnding:
    def test_terminating_asks_the_adapter_to_end_the_program(self, adapter, running):
        running.terminate()
        assert adapter.last("disconnect")["arguments"] == {"terminateDebuggee": True}

    def test_the_program_ending_by_itself_disconnects(self, adapter, running):
        adapter.event("terminated")
        assert adapter.commands()[-1] == "disconnect"

    def test_the_adapter_exiting_ends_the_session_and_fails_what_was_waiting(self, adapter, paused):
        replies = replies_to(paused.threads)
        adapter.exits(0)
        assert paused.state() is DebugState.TERMINATED
        assert (replies[0].ok, replies[0].error) == (False, "the debugger has ended")

    def test_a_session_that_ended_can_be_launched_again(self, adapter, running):
        adapter.exits(0)
        assert running.launch(DebugLaunchRequest("main.py")) is True
        assert running.state() is DebugState.STARTING

    def test_terminating_twice_or_before_a_launch_does_nothing(self, adapter, session):
        session.terminate()
        assert adapter.sent == []

    def test_the_adapter_is_stopped_if_it_does_not_leave(self, adapter, running, monkeypatch):
        monkeypatch.setattr("je_editor.adapters.debug.dap_session.DISCONNECT_GRACE_SECONDS", 0.05)
        stopped = threading.Event()
        adapter.cancel = stopped.set
        running.terminate()
        assert stopped.wait(WAIT_SECONDS)


class TestTheSocketChannel:
    """A TCP connection shaped like a binary task, for adapters that wait on a port."""

    @pytest.fixture()
    def listener(self):
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            yield server

    def test_it_satisfies_the_task_interface(self):
        channel = SocketChannel("127.0.0.1", 1)
        assert isinstance(channel, TaskHandle)
        assert (channel.state(), channel.spec.binary, channel.exit_code()) == (
            TaskState.PENDING, True, None)

    def test_bytes_go_both_ways_and_the_end_is_announced(self, listener):
        channel = SocketChannel(*listener.getsockname())
        received: list[bytes] = []
        ended = threading.Event()
        channel.output.subscribe(lambda _stream, data: received.append(data))
        channel.finished.subscribe(lambda _code: ended.set())
        assert channel.start() is True
        peer, _address = listener.accept()
        with peer:
            assert channel.write(b"ping") is True
            assert peer.recv(16) == b"ping"
            peer.sendall(b"pong")
        assert ended.wait(WAIT_SECONDS)
        assert (b"".join(received), channel.state(), channel.exit_code()) == (
            b"pong", TaskState.FINISHED, 0)
        assert channel.write(b"late") is False

    def test_nothing_listening_means_it_does_not_start(self, listener):
        address = listener.getsockname()
        listener.close()
        channel = SocketChannel(*address)
        assert channel.start() is False
        assert (channel.state(), channel.write(b"x")) == (TaskState.FAILED_TO_START, False)

    def test_cancelling_closes_the_connection(self, listener):
        channel = SocketChannel(*listener.getsockname())
        ended = threading.Event()
        channel.finished.subscribe(lambda _code: ended.set())
        channel.start()
        peer, _address = listener.accept()
        with peer:
            channel.cancel()
            assert peer.recv(16) == b""
        assert ended.wait(WAIT_SECONDS)
        assert channel.state() is TaskState.CANCELLED

    def test_it_connects_only_once(self, listener):
        channel = SocketChannel(*listener.getsockname())
        assert (channel.start(), channel.start()) == (True, False)
        channel.cancel()


class TestRequests:
    def test_a_launch_needs_a_program(self):
        with pytest.raises(JEditorServiceException):
            DebugLaunchRequest("")

    @pytest.mark.parametrize("port", [0, -1, 70000])
    def test_an_attach_needs_a_real_port(self, port):
        with pytest.raises(JEditorServiceException):
            DebugAttachRequest(port)


class TestTheDebugpyAdapter:
    def test_launch_arguments(self):
        launch = DebugLaunchRequest("main.py", ("--fast",), "C:/work", True, "C:/env/python.exe", False)
        assert debugpy_adapter.launch_arguments(launch) == {
            "request": "launch", "type": "python", "program": "main.py", "args": ["--fast"],
            "console": "internalConsole", "redirectOutput": True, "stopOnEntry": True,
            "justMyCode": False, "cwd": "C:/work", "python": ["C:/env/python.exe"]}

    def test_the_defaults_leave_the_folder_and_interpreter_to_the_adapter(self):
        arguments = debugpy_adapter.launch_arguments(DebugLaunchRequest("main.py"))
        assert "cwd" not in arguments and "python" not in arguments

    def test_attach_arguments(self):
        assert debugpy_adapter.attach_arguments(DebugAttachRequest(5678, "10.0.0.2")) == {
            "request": "attach", "type": "python", "justMyCode": True,
            "connect": {"host": "10.0.0.2", "port": 5678}}

    def test_attaching_connects_straight_to_the_waiting_program(self):
        channel = debugpy_adapter.attach_channel(DebugAttachRequest(5678, "10.0.0.2"))
        assert channel.spec.command == ("tcp", "10.0.0.2:5678")

    def test_the_adapter_runs_on_this_interpreter(self):
        assert debugpy_adapter.adapter_command() == (sys.executable, "-m", "debugpy.adapter")

    def test_it_is_registered_when_debugpy_is_installed(self):
        registry: NamedRegistry = NamedRegistry("debug adapter")
        debugpy_adapter.register_builtin_debug_adapters(registry, ScriptedAdapter)
        assert registry.names() == ["debugpy"]
        assert isinstance(registry.require("debugpy")(), DapSession)

    def test_it_is_not_registered_without_debugpy(self, monkeypatch):
        monkeypatch.setattr(debugpy_adapter, "debugpy_available", lambda: False)
        registry: NamedRegistry = NamedRegistry("debug adapter")
        debugpy_adapter.register_builtin_debug_adapters(registry, ScriptedAdapter)
        assert registry.names() == []

    def test_the_default_services_carry_the_runner_and_the_adapter(self, tmp_path):
        services = build_default_services(settings_directory=tmp_path)
        try:
            assert isinstance(services.task_runners.require(LOCAL_RUNNER), LocalTaskRunner)
            assert services.debug_adapters.names() == ["debugpy"]
        finally:
            services.shutdown()

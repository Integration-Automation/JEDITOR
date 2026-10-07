"""
Integration tests: the DAP debug session driving the real debugpy adapter.

Each test starts an adapter process and a program under it, so these are slower
than the rest; what they prove is that the session's handshake, its queries and
its control commands work against an adapter nobody here wrote.
"""
from __future__ import annotations

import queue
import socket
import subprocess
import sys
import threading
import time

import pytest

from je_editor.adapters.debug.debugpy_adapter import debugpy_available, debugpy_session
from je_editor.adapters.process.local_task_runner import LocalTaskRunner
from je_editor.core.debug.debug_session import (
    Breakpoint, DebugAttachRequest, DebugLaunchRequest, DebugReply, DebugState, StepKind, StopEvent
)
from je_editor.core.uri.resource_uri import to_uri, uri_key

pytestmark = pytest.mark.skipif(not debugpy_available(), reason="debugpy is not installed")

# A debugger starts two processes and a socket between them; a busy machine needs room.
WAIT_SECONDS = 60
ADD_LINE = 5
RETURN_LINE = 6
PROGRAM = '''\
import sys


def add(first, second):
    total = first + second
    return total


values = [add(number, 10) for number in range(3)]
print("done", values)
'''
FAILING = "numbers = [1, 0]\nprint(numbers[0] / numbers[1])\n"
LOOPING = "import time\n\nwhile True:\n    time.sleep(0.05)\n"


class Watcher:
    """Collects what a session announces from its own thread."""

    def __init__(self, session) -> None:
        self.stops: queue.Queue[StopEvent] = queue.Queue()
        self.output: list[str] = []
        self.states: list[DebugState] = []
        self._ended = threading.Event()
        self._running = threading.Event()
        session.stopped.subscribe(self.stops.put)
        session.output.subscribe(lambda event: self.output.append(event.text))
        session.state_changed.subscribe(self._on_state)

    def _on_state(self, state: DebugState) -> None:
        self.states.append(state)
        if state is DebugState.RUNNING:
            self._running.set()
        if state is DebugState.TERMINATED:
            self._ended.set()

    def next_stop(self) -> StopEvent:
        return self.stops.get(timeout=WAIT_SECONDS)

    def wait_until_running(self) -> bool:
        return self._running.wait(WAIT_SECONDS)

    def wait_until_ended(self) -> bool:
        return self._ended.wait(WAIT_SECONDS)


def ask(query, *arguments):
    """Put a query to the session and wait for its reply."""
    answered = threading.Event()
    replies: list[DebugReply] = []

    def receive(reply: DebugReply) -> None:
        replies.append(reply)
        answered.set()

    query(*arguments, receive)
    assert answered.wait(WAIT_SECONDS), "the debugger did not answer"
    assert replies[0].ok, replies[0].error
    return replies[0].value


def named(variables) -> dict[str, str]:
    return {variable.name: variable.value for variable in variables}


@pytest.fixture()
def runner():
    local = LocalTaskRunner()
    yield local
    local.shutdown()


@pytest.fixture()
def session(runner):
    built = debugpy_session(runner)
    yield built
    built.terminate()


def write_program(tmp_path, text: str) -> tuple[str, str]:
    path = tmp_path / "program.py"
    path.write_text(text, encoding="utf-8")
    return str(path), to_uri(path)


def locals_of(session, frame) -> dict[str, str]:
    scopes = ask(session.scopes, frame.frame_id)
    local_scope = next(scope for scope in scopes if scope.name.lower().startswith("local"))
    return named(ask(session.variables, local_scope.variables_reference))


class TestLaunching:
    def test_a_breakpoint_stops_the_program_and_everything_can_be_inspected(self, session, tmp_path):
        program, uri = write_program(tmp_path, PROGRAM)
        watcher = Watcher(session)
        session.set_breakpoints(uri, [Breakpoint(uri, ADD_LINE)])
        assert session.launch(DebugLaunchRequest(program, working_directory=str(tmp_path))) is True

        stop = watcher.next_stop()
        assert (stop.reason, session.state()) == ("breakpoint", DebugState.PAUSED)
        assert stop.thread_id in [thread.thread_id for thread in ask(session.threads)]

        frames = ask(session.stack_trace, stop.thread_id)
        assert (frames[0].name, frames[0].line) == ("add", ADD_LINE)
        assert uri_key(frames[0].uri) == uri_key(uri)
        assert locals_of(session, frames[0]) == {"first": "0", "second": "10"}
        assert ask(session.evaluate, "first + second", frames[0].frame_id).value == "10"

        session.step(StepKind.OVER)
        assert watcher.next_stop().reason == "step"
        frames = ask(session.stack_trace, stop.thread_id)
        assert frames[0].line == RETURN_LINE
        assert locals_of(session, frames[0])["total"] == "10"

        session.step(StepKind.OUT)
        assert watcher.next_stop().reason == "step"
        assert ask(session.stack_trace, stop.thread_id)[0].name != "add"

        session.resume()
        assert watcher.next_stop().reason == "breakpoint"
        frames = ask(session.stack_trace, stop.thread_id)
        assert locals_of(session, frames[0])["first"] == "1"

        session.terminate()
        assert watcher.wait_until_ended()
        assert session.state() is DebugState.TERMINATED

    def test_a_conditional_breakpoint_stops_only_when_its_condition_holds(self, session, tmp_path):
        program, uri = write_program(tmp_path, PROGRAM)
        watcher = Watcher(session)
        session.set_breakpoints(uri, [Breakpoint(uri, ADD_LINE, "first == 2")])
        session.launch(DebugLaunchRequest(program))
        stop = watcher.next_stop()
        frames = ask(session.stack_trace, stop.thread_id)
        assert locals_of(session, frames[0])["first"] == "2"

    def test_stopping_on_entry_then_running_to_the_end(self, session, tmp_path):
        program, _uri = write_program(tmp_path, PROGRAM)
        watcher = Watcher(session)
        session.launch(DebugLaunchRequest(program, stop_on_entry=True))
        stop = watcher.next_stop()
        assert stop.reason == "entry"
        assert ask(session.stack_trace, stop.thread_id)[0].line == 1
        session.resume()
        assert watcher.wait_until_ended()
        assert "done [10, 11, 12]" in "".join(watcher.output)

    def test_stepping_into_a_call(self, session, tmp_path):
        program, uri = write_program(tmp_path, PROGRAM)
        watcher = Watcher(session)
        session.set_breakpoints(uri, [Breakpoint(uri, RETURN_LINE + 3)])
        session.launch(DebugLaunchRequest(program))
        stop = watcher.next_stop()
        names = set()
        for _attempt in range(4):
            session.step(StepKind.INTO)
            watcher.next_stop()
            names.add(ask(session.stack_trace, stop.thread_id)[0].name)
        assert "add" in names

    def test_an_uncaught_exception_stops_the_program_and_can_be_asked_about(self, session, tmp_path):
        program, _uri = write_program(tmp_path, FAILING)
        watcher = Watcher(session)
        session.launch(DebugLaunchRequest(program))
        stop = watcher.next_stop()
        assert stop.reason == "exception"
        info = ask(session.exception_info, stop.thread_id)
        assert "ZeroDivisionError" in info.exception_id
        assert "division by zero" in info.description

    def test_a_running_program_can_be_paused(self, session, tmp_path):
        program, _uri = write_program(tmp_path, LOOPING)
        watcher = Watcher(session)
        session.launch(DebugLaunchRequest(program))
        assert watcher.wait_until_running()
        threads = ask(session.threads)
        session.pause(threads[0].thread_id)
        assert watcher.next_stop().reason == "pause"
        assert session.state() is DebugState.PAUSED

    def test_a_program_that_is_not_there_ends_the_session(self, session, tmp_path):
        watcher = Watcher(session)
        session.launch(DebugLaunchRequest(str(tmp_path / "missing.py")))
        assert watcher.wait_until_ended()
        assert session.state() is DebugState.TERMINATED


class TestAttaching:
    def test_attaching_to_a_program_that_waits_for_a_debugger(self, session, tmp_path):
        program, uri = write_program(tmp_path, PROGRAM)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        waiting = subprocess.Popen(
            [sys.executable, "-m", "debugpy", "--listen", f"127.0.0.1:{port}", "--wait-for-client",
             program], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            watcher = Watcher(session)
            session.set_breakpoints(uri, [Breakpoint(uri, ADD_LINE)])
            # The program needs a moment before its port accepts a debugger.
            deadline = time.monotonic() + WAIT_SECONDS
            while not session.attach(DebugAttachRequest(port)):
                assert time.monotonic() < deadline, "the program never listened"
                time.sleep(0.2)
            stop = watcher.next_stop()
            assert stop.reason == "breakpoint"
            assert ask(session.stack_trace, stop.thread_id)[0].name == "add"
            session.terminate()
            assert watcher.wait_until_ended()
        finally:
            waiting.kill()
            waiting.wait(WAIT_SECONDS)

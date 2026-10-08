"""Tests for the service container and the debug, task, remote and AI interfaces."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QCoreApplication

from je_editor.core.ai.ai_provider import (
    AIProvider, CancelToken, ChatMessage, ChatRequest, ChatResponse, ChatRole, ModelInfo
)
from je_editor.core.debug.debug_session import (
    Breakpoint, DebugLaunchRequest, DebugReply, DebugSession, DebugState, StepKind
)
from je_editor.core.diagnostics.diagnostic_model import Diagnostic, TextRange
from je_editor.core.document.document_model import TextDocument
from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import (
    OutputStream, TaskHandle, TaskRunner, TaskSpec, TaskState
)
from je_editor.core.remote.remote_session import RemoteSession, RemoteState
from je_editor.core.services.editor_services import EditorServices
from je_editor.core.uri.resource_uri import to_uri, uri_scheme
from je_editor.core.workspace.workspace_model import Workspace
from je_editor.utils.exception.exceptions import JEditorServiceException

REMOTE_ROOT_URI = "ssh://build-host/srv/project"


class FakeTask:
    """A task that plays back fixed output instead of starting a process."""

    def __init__(self, spec: TaskSpec) -> None:
        self.spec = spec
        self.output = EventHook("task output")
        self.finished = EventHook("task finished")
        self._state = TaskState.PENDING
        self._exit_code: int | None = None
        self.written: list[str] = []

    def state(self) -> TaskState:
        return self._state

    def exit_code(self) -> int | None:
        return self._exit_code

    def start(self) -> bool:
        self._state = TaskState.RUNNING
        self.output.emit(OutputStream.STDOUT, f"ran {' '.join(self.spec.command)}")
        self._finish(TaskState.FINISHED, 0)
        return True

    def write(self, text: str) -> bool:
        self.written.append(text)
        return True

    def close_input(self) -> None:
        self.written.append(None)

    def cancel(self) -> None:
        if self._state in (TaskState.PENDING, TaskState.RUNNING):
            self._finish(TaskState.CANCELLED, -1)

    def _finish(self, state: TaskState, exit_code: int) -> None:
        self._state = state
        self._exit_code = exit_code
        self.finished.emit(exit_code)


class FakeRunner:
    """A task runner that hands out fake tasks and remembers being shut down."""

    def __init__(self) -> None:
        self.created: list[FakeTask] = []
        self.shut_down = False

    def create(self, spec: TaskSpec) -> FakeTask:
        task = FakeTask(spec)
        self.created.append(task)
        return task

    def shutdown(self) -> None:
        self.shut_down = True
        for task in self.created:
            task.cancel()


class FakeDebugSession:
    """A debug session that only tracks its state and what it was told."""

    def __init__(self) -> None:
        self.state_changed = EventHook("debug state changed")
        self.stopped = EventHook("debug stopped")
        self.output = EventHook("debug output")
        self.breakpoints_reported = EventHook("debug breakpoints reported")
        self._state = DebugState.IDLE
        self.breakpoints: dict[str, list[Breakpoint]] = {}

    def state(self) -> DebugState:
        return self._state

    def _move_to(self, state: DebugState) -> None:
        self._state = state
        self.state_changed.emit(state)

    def launch(self, request: DebugLaunchRequest) -> bool:
        self._move_to(DebugState.PAUSED if request.stop_on_entry else DebugState.RUNNING)
        return True

    def attach(self, request) -> bool:
        self._move_to(DebugState.RUNNING)
        return True

    def set_breakpoints(self, uri: str, breakpoints) -> None:
        self.breakpoints[uri] = list(breakpoints)

    def resume(self, thread_id: int = 0) -> None:
        self._move_to(DebugState.RUNNING)

    def pause(self, thread_id: int = 0) -> None:
        self._move_to(DebugState.PAUSED)

    def step(self, kind: StepKind, thread_id: int = 0) -> None:
        self._move_to(DebugState.PAUSED)

    def threads(self, on_reply) -> None:
        on_reply(DebugReply(()))

    def stack_trace(self, thread_id: int, on_reply) -> None:
        on_reply(DebugReply(()))

    def scopes(self, frame_id: int, on_reply) -> None:
        on_reply(DebugReply(()))

    def variables(self, reference: int, on_reply) -> None:
        on_reply(DebugReply(()))

    def evaluate(self, expression: str, frame_id: int, on_reply) -> None:
        on_reply(DebugReply(None, "the fake evaluates nothing"))

    def exception_info(self, thread_id: int, on_reply) -> None:
        on_reply(DebugReply(None))

    def terminate(self) -> None:
        self._move_to(DebugState.TERMINATED)


class FakeRemoteSession:
    """A remote session that connects instantly and runs tasks on a fake runner."""

    def __init__(self, authority: str) -> None:
        self.authority = authority
        self.state_changed = EventHook("remote state changed")
        self._state = RemoteState.DISCONNECTED
        self._runner = FakeRunner()

    def state(self) -> RemoteState:
        return self._state

    def connect(self) -> bool:
        self._state = RemoteState.CONNECTED
        self.state_changed.emit(self._state)
        return True

    def last_error(self) -> str:
        return ""

    def reconnect(self) -> bool:
        return self.connect()

    def disconnect(self) -> None:
        self._state = RemoteState.DISCONNECTED
        self.state_changed.emit(self._state)

    def task_runner(self) -> FakeRunner:
        return self._runner

    def file_system(self):
        return None

    def forward_port(self, remote_port: int, remote_host: str = "127.0.0.1", local_port: int = 0):
        return None

    def interpreters(self, root: str = "") -> tuple:
        return ()


class EchoProvider:
    """An AI provider that answers with the last message, word by word."""

    name = "echo"

    def models(self) -> list[ModelInfo]:
        return [ModelInfo("echo-1", "Echo", supports_streaming=True)]

    def complete(self, request: ChatRequest, on_text=None, cancel=None) -> ChatResponse:
        said: list[str] = []
        for word in request.messages[-1].content.split():
            if cancel is not None and cancel.cancelled:
                return ChatResponse(" ".join(said), "echo-1", cancelled=True)
            said.append(word)
            if on_text is not None:
                on_text(word)
        return ChatResponse(" ".join(said), "echo-1", len(request.messages), len(said))


class TestBuildingTheServices:
    def test_no_application_object_is_created(self):
        before = QCoreApplication.instance()
        EditorServices()
        assert QCoreApplication.instance() is before

    def test_it_starts_with_an_empty_workspace(self):
        services = EditorServices()
        assert services.workspace.roots == ()
        assert len(services.documents) == 0
        assert len(services.diagnostics) == 0

    def test_a_given_workspace_is_used(self, tmp_path):
        workspace = Workspace.single_root(tmp_path)
        assert EditorServices(workspace).workspace is workspace

    def test_two_sets_of_services_share_nothing(self, tmp_path):
        first, second = EditorServices(), EditorServices()
        first.workspace.add_root(tmp_path)
        first.documents.open(TextDocument(to_uri(tmp_path / "a.py")))
        first.ai_providers.register("echo", EchoProvider())
        assert second.workspace.roots == ()
        assert len(second.documents) == 0
        assert second.ai_providers.names() == []

    def test_every_provider_registry_starts_empty(self):
        services = EditorServices()
        assert [len(registry) for registry in (
            services.debug_adapters, services.task_runners,
            services.remote_transports, services.ai_providers)] == [0, 0, 0, 0]


class TestShuttingDown:
    @pytest.fixture()
    def busy(self, tmp_path):
        services = EditorServices(Workspace.single_root(tmp_path))
        uri = to_uri(tmp_path / "a.py")
        services.documents.open(TextDocument(uri, "import os\n", "python"))
        services.diagnostics.publish("ruff", uri, [Diagnostic("unused", TextRange.from_lines(1))])
        services.task_runners.register("local", FakeRunner())
        return services

    def test_task_runners_are_shut_down_and_removed(self, busy):
        runner = busy.task_runners.require("local")
        busy.shutdown()
        assert runner.shut_down is True
        assert busy.task_runners.names() == []

    def test_a_task_that_has_not_finished_is_cancelled(self, busy):
        task = busy.task_runners.require("local").create(TaskSpec(("python", "server.py")))
        busy.shutdown()
        assert task.state() is TaskState.CANCELLED

    def test_documents_and_diagnostics_are_released(self, busy):
        busy.shutdown()
        assert len(busy.documents) == 0
        assert len(busy.diagnostics) == 0

    def test_open_documents_are_announced_as_closed(self, busy):
        closed = []
        busy.documents.closed.subscribe(lambda document: closed.append(document.uri))
        expected = [document.uri for document in busy.documents.documents()]
        busy.shutdown()
        assert closed == expected

    def test_shutting_down_twice_is_harmless(self, busy):
        busy.shutdown()
        busy.task_runners.register("late", FakeRunner())
        busy.shutdown()
        assert busy.is_shut_down
        assert busy.task_runners.require("late").shut_down is False


class TestTaskInterface:
    def test_the_fakes_satisfy_the_protocols(self):
        runner = FakeRunner()
        assert isinstance(runner, TaskRunner)
        assert isinstance(runner.create(TaskSpec(("python", "-V"))), TaskHandle)

    def test_a_command_given_as_a_list_is_frozen(self):
        command = ["python", "main.py"]
        spec = TaskSpec(command)
        command.append("--injected")
        assert spec.command == ("python", "main.py")

    def test_the_environment_is_copied_and_cannot_be_changed(self):
        environment = {"PYTHONUTF8": "1"}
        spec = TaskSpec(("python", "main.py"), environment=environment)
        environment["INJECTED"] = "1"
        assert dict(spec.environment) == {"PYTHONUTF8": "1"}
        with pytest.raises(TypeError):
            spec.environment["INJECTED"] = "1"

    @pytest.mark.parametrize("command", [(), [], "python main.py", ("python", ""), ("python", 3)])
    def test_a_command_that_is_not_an_argument_list_is_refused(self, command):
        with pytest.raises(JEditorServiceException, match="task command"):
            TaskSpec(command)

    def test_subscribing_before_the_start_catches_the_first_output(self):
        task = FakeRunner().create(TaskSpec(("python", "main.py"), name="Run main"))
        output, codes = [], []
        task.output.subscribe(lambda stream, text: output.append((stream, text)))
        task.finished.subscribe(codes.append)
        assert task.state() is TaskState.PENDING
        assert task.start() is True
        assert output == [(OutputStream.STDOUT, "ran python main.py")]
        assert codes == [0]
        assert (task.state(), task.exit_code()) == (TaskState.FINISHED, 0)


class TestDebugInterface:
    def test_the_fake_satisfies_the_protocol(self):
        assert isinstance(FakeDebugSession(), DebugSession)

    def test_a_session_without_the_queries_does_not(self):
        class ControlOnly:
            state_changed = EventHook("state")

            def state(self) -> DebugState:
                return DebugState.IDLE

        assert not isinstance(ControlOnly(), DebugSession)

    def test_a_reply_is_ok_unless_it_carries_an_error(self):
        replies: list[DebugReply] = []
        session = FakeDebugSession()
        session.threads(replies.append)
        session.evaluate("x", 0, replies.append)
        assert [(reply.ok, reply.value) for reply in replies] == [(True, ()), (False, None)]

    def test_a_launch_needs_a_program(self):
        with pytest.raises(JEditorServiceException, match="needs a program"):
            DebugLaunchRequest(program="")

    def test_an_adapter_is_built_from_the_registry_and_driven(self, tmp_path):
        services = EditorServices()
        services.debug_adapters.register("fake", FakeDebugSession)
        session = services.debug_adapters.require("fake")()
        states = []
        session.state_changed.subscribe(states.append)
        uri = to_uri(tmp_path / "main.py")
        session.set_breakpoints(uri, [Breakpoint(uri, 3), Breakpoint(uri, 9, condition="x > 1")])
        session.launch(DebugLaunchRequest(str(tmp_path / "main.py"), stop_on_entry=True))
        session.step(StepKind.OVER)
        session.resume()
        session.terminate()
        assert states == [
            DebugState.PAUSED, DebugState.PAUSED, DebugState.RUNNING, DebugState.TERMINATED]
        assert [point.line for point in session.breakpoints[uri]] == [3, 9]

    def test_an_unknown_adapter_is_reported_with_the_known_ones(self):
        services = EditorServices()
        services.debug_adapters.register("fake", FakeDebugSession)
        with pytest.raises(JEditorServiceException, match="registered: fake"):
            services.debug_adapters.require("dap")


class TestRemoteInterface:
    def test_the_fake_satisfies_the_protocol(self):
        assert isinstance(FakeRemoteSession("build-host"), RemoteSession)

    def test_a_transport_is_found_by_the_scheme_of_a_root(self):
        services = EditorServices()
        services.remote_transports.register("ssh", FakeRemoteSession)
        transport = services.remote_transports.require(uri_scheme(REMOTE_ROOT_URI))
        session = transport("build-host")
        assert session.connect() is True
        assert (session.authority, session.state()) == ("build-host", RemoteState.CONNECTED)

    def test_a_remote_task_looks_like_a_local_one(self):
        session = FakeRemoteSession("build-host")
        session.connect()
        task = session.task_runner().create(TaskSpec(("pytest", "-q")))
        assert isinstance(task, TaskHandle)
        assert task.start() is True


class TestAIProviderInterface:
    @pytest.fixture()
    def request_for_reply(self):
        return ChatRequest(
            (ChatMessage(ChatRole.USER, "explain this function please"),),
            system_prompt="Answer briefly.")

    def test_the_fake_satisfies_the_protocol(self):
        assert isinstance(EchoProvider(), AIProvider)

    def test_a_provider_is_chosen_by_name(self, request_for_reply):
        services = EditorServices()
        services.ai_providers.register(EchoProvider.name, EchoProvider())
        response = services.ai_providers.require("echo").complete(request_for_reply)
        assert response.text == "explain this function please"
        assert (response.input_tokens, response.output_tokens) == (1, 4)

    def test_text_arrives_piece_by_piece_when_asked_for(self, request_for_reply):
        pieces = []
        EchoProvider().complete(request_for_reply, on_text=pieces.append)
        assert pieces == ["explain", "this", "function", "please"]

    def test_a_cancel_stops_the_reply_part_way(self, request_for_reply):
        cancel = CancelToken()
        pieces = []

        def stop_after_two(piece: str) -> None:
            pieces.append(piece)
            if len(pieces) == 2:
                cancel.cancel()

        response = EchoProvider().complete(request_for_reply, stop_after_two, cancel)
        assert response.cancelled is True
        assert response.text == "explain this"

    def test_a_token_is_not_cancelled_until_asked(self):
        assert CancelToken().cancelled is False

    def test_the_models_describe_themselves(self):
        model = EchoProvider().models()[0]
        assert (model.model_id, model.display_name, model.supports_streaming) == (
            "echo-1", "Echo", True)

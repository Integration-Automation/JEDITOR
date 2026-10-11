"""Tests for remote sessions: the pool, and the SSH transport driven through a stand-in ssh program."""
from __future__ import annotations

import queue
import shlex
import socket
import sys
import threading
from pathlib import Path

import pytest

from je_editor.adapters.debug.dap_session import DapSession
from je_editor.adapters.debug.debugpy_adapter import (
    attach_arguments, debugpy_available, launch_arguments
)
from je_editor.adapters.default_services import build_default_services
from je_editor.adapters.process.local_task_runner import LocalTaskRunner
from je_editor.adapters.remote.ssh_session import (
    DEFAULT_OPTIONS, SshCommand, SshRemoteSession, SshTarget, parse_authority, run_to_completion
)
from je_editor.core.debug.debug_session import Breakpoint, DebugLaunchRequest
from je_editor.core.process.task_service import OutputStream, TaskRunner, TaskSpec
from je_editor.core.registry.named_registry import NamedRegistry
from je_editor.core.remote.remote_pool import RemoteSessionPool, split_remote_uri
from je_editor.core.remote.remote_session import (
    PortForward, RemoteEntry, RemoteFileSystem, RemoteSession, RemoteState
)
from je_editor.core.uri.resource_uri import to_uri
from je_editor.utils.exception.exceptions import JEditorServiceException

FAKE_SSH = (sys.executable, str(Path(__file__).with_name("fake_ssh.py")))
WAIT_SECONDS = 60


@pytest.fixture()
def runner():
    local = LocalTaskRunner()
    yield local
    local.shutdown()


def session_to(authority: str, runner: LocalTaskRunner) -> SshRemoteSession:
    return SshRemoteSession(authority, runner, program=FAKE_SSH)


@pytest.fixture()
def session(runner):
    connected = session_to("me@build-box", runner)
    assert connected.connect() is True
    yield connected
    connected.disconnect()


class TestTheAuthority:
    @pytest.mark.parametrize("authority, expected", [
        ("build-box", SshTarget("build-box")),
        ("me@build-box", SshTarget("build-box", "me")),
        ("me@10.0.0.2:2222", SshTarget("10.0.0.2", "me", 2222)),
        ("deploy_user@host.example.com", SshTarget("host.example.com", "deploy_user")),
        ("[::1]:22", SshTarget("::1", "", 22)),
    ])
    def test_a_usable_authority(self, authority, expected):
        assert parse_authority(authority) == expected

    @pytest.mark.parametrize("authority", [
        "", "-oProxyCommand=calc", "me@-oProxyCommand=calc", "-l@host", "host name", "me@",
        "@host", "host:port", "host:99999", "me;rm@host", "host/path", "me@host:22:22", "$(id)",
    ])
    def test_an_authority_that_is_refused(self, authority):
        with pytest.raises(JEditorServiceException):
            parse_authority(authority)

    def test_the_destination_carries_the_user_when_there_is_one(self):
        assert (SshTarget("host", "me").destination, SshTarget("host").destination) == (
            "me@host", "host")


class TestTheCommandLine:
    def test_options_then_the_end_of_options_then_the_destination(self):
        command = SshCommand(SshTarget("host", "me", 2222)).remote(["ls"])
        assert command == ("ssh", *DEFAULT_OPTIONS, "-p", "2222", "--", "me@host", "ls")

    def test_the_remote_command_is_one_quoted_argument(self):
        arguments = ["python3", "-c", "print('a b')", "file with space.py", "x;rm -rf /", "$HOME"]
        command = SshCommand(SshTarget("host")).remote(arguments)
        assert command[-2] == "host"
        assert shlex.split(command[-1]) == arguments

    def test_no_prompt_is_ever_allowed(self):
        assert "BatchMode=yes" in SshCommand(SshTarget("host")).remote(["true"])

    def test_forwarding_runs_no_command(self):
        command = SshCommand(SshTarget("host")).forward(9000, "127.0.0.1", 5678)
        assert command[-2:] == ("--", "host")
        assert "-N" in command and "127.0.0.1:9000:127.0.0.1:5678" in command
        assert "ExitOnForwardFailure=yes" in command


class TestRemoteUris:
    def test_a_remote_uri_is_split(self):
        assert split_remote_uri("SSH://me@build-box:2222/home/me/main.py") == (
            "ssh", "me@build-box:2222", "/home/me/main.py")

    def test_no_path_means_the_root(self):
        assert split_remote_uri("ssh://build-box") == ("ssh", "build-box", "/")

    @pytest.mark.parametrize("uri", ["", "main.py", "C:/work/main.py", "ssh:///home/me", "file:///x"])
    def test_what_is_not_a_remote_uri_is_refused(self, uri):
        with pytest.raises(JEditorServiceException):
            split_remote_uri(uri)


class TestThePool:
    @pytest.fixture()
    def pool(self, runner):
        transports: NamedRegistry = NamedRegistry("remote transport")
        transports.register("ssh", lambda authority: session_to(authority, runner))
        return RemoteSessionPool(transports)

    def test_two_resources_on_one_machine_share_a_session(self, pool):
        first = pool.session_for("ssh://me@build-box/home/me/a.py")
        assert pool.session_for("ssh://me@build-box/srv/b.py") is first
        assert pool.session_for("ssh://me@other-box/a.py") is not first
        assert len(pool.sessions()) == 2

    def test_a_session_is_built_without_connecting(self, pool):
        assert pool.session_for("ssh://build-box/x").state() is RemoteState.DISCONNECTED

    def test_an_unknown_scheme_is_reported_with_the_known_ones(self, pool):
        with pytest.raises(JEditorServiceException, match="registered: ssh"):
            pool.session_for("telnet://build-box/x")

    def test_shutting_down_disconnects_and_forgets_every_session(self, pool):
        session = pool.session_for("ssh://build-box/x")
        session.connect()
        pool.shutdown()
        assert (session.state(), pool.sessions()) == (RemoteState.DISCONNECTED, [])

    def test_the_default_services_know_ssh(self, tmp_path):
        services = build_default_services(settings_directory=tmp_path)
        try:
            assert services.remote_transports.names() == ["ssh"]
            session = services.remotes.session_for("ssh://me@build-box/home/me")
            assert isinstance(session, SshRemoteSession) and session.authority == "me@build-box"
        finally:
            services.shutdown()


class TestConnecting:
    def test_the_session_satisfies_the_interfaces(self, session):
        assert isinstance(session, RemoteSession)
        assert isinstance(session.file_system(), RemoteFileSystem)
        assert isinstance(session.task_runner(), TaskRunner)

    def test_connecting_goes_through_connecting_to_connected(self, runner):
        session = session_to("build-box", runner)
        states: list[RemoteState] = []
        session.state_changed.subscribe(states.append)
        assert session.connect() is True
        assert states == [RemoteState.CONNECTING, RemoteState.CONNECTED]
        assert session.last_error() == ""

    def test_a_machine_that_cannot_be_reached_fails_with_the_reason(self, runner):
        session = session_to("unreachable-box", runner)
        assert session.connect() is False
        assert session.state() is RemoteState.FAILED
        assert "Connection refused" in session.last_error()

    def test_a_machine_without_python3_falls_back_to_python(self, runner):
        session = session_to("nopython3-box", runner)
        assert session.connect() is True
        assert session.file_system().stat("/definitely/not/here") is None

    def test_reconnecting_says_so(self, session):
        states: list[RemoteState] = []
        session.state_changed.subscribe(states.append)
        assert session.reconnect() is True
        assert states == [RemoteState.RECONNECTING, RemoteState.CONNECTED]

    def test_nothing_can_be_asked_before_connecting(self, runner):
        session = session_to("build-box", runner)
        with pytest.raises(JEditorServiceException, match="Not connected"):
            session.file_system().read_bytes("/etc/hostname")

    def test_disconnecting_ends_the_session(self, session):
        session.disconnect()
        assert session.state() is RemoteState.DISCONNECTED
        with pytest.raises(JEditorServiceException):
            session.file_system().stat("/")

    def test_an_authority_that_is_refused_never_builds_a_session(self, runner):
        with pytest.raises(JEditorServiceException):
            session_to("-oProxyCommand=calc", runner)


class TestTheFileSystem:
    def test_bytes_written_are_the_bytes_read(self, session, tmp_path):
        path = (tmp_path / "data.bin").as_posix()
        content = bytes(range(256)) * 40
        session.file_system().write_bytes(path, content)
        assert session.file_system().read_bytes(path) == content
        assert Path(path).read_bytes() == content

    def test_writing_makes_the_folders_it_needs(self, session, tmp_path):
        path = (tmp_path / "new" / "deeper" / "note.txt").as_posix()
        session.file_system().write_bytes(path, b"hello")
        assert Path(path).read_bytes() == b"hello"

    def test_an_empty_file_and_a_name_with_spaces_and_unicode(self, session, tmp_path):
        path = (tmp_path / "空 白 file's.txt").as_posix()
        session.file_system().write_bytes(path, b"")
        assert session.file_system().read_bytes(path) == b""

    def test_a_directory_lists_folders_first_then_by_name(self, session, tmp_path):
        (tmp_path / "zeta").mkdir()
        (tmp_path / "Alpha.py").write_bytes(b"12345")
        (tmp_path / "beta.py").write_bytes(b"")
        entries = session.file_system().list_directory(tmp_path.as_posix())
        assert [(entry.name, entry.is_directory, entry.size) for entry in entries] == [
            ("zeta", True, 0), ("Alpha.py", False, 5), ("beta.py", False, 0)]
        assert all(isinstance(entry, RemoteEntry) and entry.modified > 0 for entry in entries)
        assert Path(entries[1].path) == tmp_path / "Alpha.py"

    def test_looking_a_path_up(self, session, tmp_path):
        (tmp_path / "main.py").write_bytes(b"abc")
        found = session.file_system().stat((tmp_path / "main.py").as_posix())
        assert (found.name, found.is_directory, found.size) == ("main.py", False, 3)
        assert session.file_system().stat(tmp_path.as_posix()).is_directory is True
        assert session.file_system().stat((tmp_path / "missing").as_posix()) is None

    def test_what_cannot_be_done_raises_with_the_remote_reason(self, session, tmp_path):
        with pytest.raises(JEditorServiceException, match="FileNotFoundError"):
            session.file_system().read_bytes((tmp_path / "missing.py").as_posix())
        with pytest.raises(JEditorServiceException, match="list failed"):
            session.file_system().list_directory((tmp_path / "missing").as_posix())


class TestRunningTasks:
    def test_a_task_runs_remotely_in_its_folder_with_its_environment(self, session, tmp_path):
        code = "import os; print(os.getcwd()); print(os.environ['REMOTE_PROBE'])"
        task = session.task_runner().create(TaskSpec(
            (sys.executable, "-c", code), working_directory=str(tmp_path),
            environment={"REMOTE_PROBE": "a value; with $pecial 'chars'"}, binary=True))
        done = run_to_completion(task)
        lines = done.output.decode().splitlines()
        assert done.exit_code == 0
        assert (Path(lines[0]), lines[1]) == (tmp_path, "a value; with $pecial 'chars'")

    def test_the_exit_code_comes_back(self, session):
        task = session.task_runner().create(TaskSpec((sys.executable, "-c", "raise SystemExit(7)"),
                                                     binary=True))
        assert run_to_completion(task).exit_code == 7

    def test_text_output_and_input_work_like_a_local_task(self, session):
        task = session.task_runner().create(TaskSpec((sys.executable, "-c", "print(input().upper())")))
        written: list[str] = []
        ended = threading.Event()
        task.output.subscribe(lambda stream, text: written.append(text)
                              if stream is OutputStream.STDOUT else None)
        task.finished.subscribe(lambda _code: ended.set())
        task.start()
        task.write("quiet\n")
        assert ended.wait(WAIT_SECONDS)
        assert "".join(written).strip() == "QUIET"

    def test_interpreters_are_found_with_their_versions(self, session, tmp_path):
        found = session.interpreters(tmp_path.as_posix())
        # The interpreter that runs the helper is always one of them.
        assert Path(sys.executable) in [Path(interpreter.path) for interpreter in found]
        assert all(interpreter.version.count(".") == 2 for interpreter in found)
        assert len({interpreter.path for interpreter in found}) == len(found)

    def test_a_run_that_times_out_is_stopped(self, session):
        task = session.task_runner().create(TaskSpec(
            (sys.executable, "-c", "import time; time.sleep(120)"), binary=True))
        done = run_to_completion(task, timeout=1.0)
        assert (done.exit_code, done.errors) == (None, b"timed out")


class TestForwardingAPort:
    @pytest.fixture()
    def echo_port(self):
        """A local server that sends back whatever it receives, in upper case."""
        with socket.socket() as server:
            server.bind(("127.0.0.1", 0))
            server.listen()

            def serve() -> None:
                try:
                    while True:
                        client, _address = server.accept()
                        with client:
                            client.sendall(client.recv(64).upper())
                except OSError:
                    return

            threading.Thread(target=serve, daemon=True).start()
            yield server.getsockname()[1]

    def test_the_local_port_reaches_the_remote_one(self, session, echo_port):
        forward = session.forward_port(echo_port)
        assert isinstance(forward, PortForward)
        assert (forward.remote_port, forward.is_open()) == (echo_port, True)
        answer = b""
        for _attempt in range(100):
            try:
                with socket.create_connection(("127.0.0.1", forward.local_port), timeout=5) as client:
                    client.sendall(b"ping")
                    answer = client.recv(64)
                break
            except OSError:
                threading.Event().wait(0.1)
        assert answer == b"PING"
        forward.close()

    def test_disconnecting_stops_every_forward(self, session, echo_port, runner):
        forward = session.forward_port(echo_port)
        session.disconnect()
        runner.shutdown()
        for _attempt in range(100):
            if not forward.is_open():
                break
            threading.Event().wait(0.1)
        assert forward.is_open() is False

    @pytest.mark.parametrize("remote_port, host, local_port", [
        (0, "127.0.0.1", 0), (70000, "127.0.0.1", 0), (80, "-oProxyCommand=x", 0), (80, "a b", 0),
        (80, "127.0.0.1", 70000),
    ])
    def test_a_forward_that_makes_no_sense_is_refused(self, session, remote_port, host, local_port):
        with pytest.raises(JEditorServiceException):
            session.forward_port(remote_port, host, local_port)


@pytest.mark.skipif(not debugpy_available(), reason="debugpy is not installed")
class TestDebuggingThroughTheRemoteRunner:
    def test_the_same_debug_session_runs_its_adapter_remotely(self, session, tmp_path):
        """A debug adapter started through the remote runner needs nothing else to change."""
        program = tmp_path / "program.py"
        program.write_text("total = 0\nfor number in range(3):\n    total += number\nprint(total)\n",
                           encoding="utf-8")
        debugging = DapSession((sys.executable, "-m", "debugpy.adapter"), session.task_runner(),
                               "debugpy", launch_arguments, attach_arguments)
        stops: queue.Queue = queue.Queue()
        debugging.stopped.subscribe(stops.put)
        uri = to_uri(program)
        debugging.set_breakpoints(uri, [Breakpoint(uri, 3, "number == 2")])
        try:
            assert debugging.launch(DebugLaunchRequest(str(program))) is True
            stop = stops.get(timeout=WAIT_SECONDS)
            frames: queue.Queue = queue.Queue()
            debugging.stack_trace(stop.thread_id, frames.put)
            assert stop.reason == "breakpoint"
            assert frames.get(timeout=WAIT_SECONDS).value[0].line == 3
        finally:
            debugging.terminate()

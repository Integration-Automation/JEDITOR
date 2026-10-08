"""
以系統的 ssh 指令實作的遠端工作階段
The remote session, implemented with the system's ssh command.

每一個遠端操作都是在本機啟動一個 ``ssh`` 程序：它的標準輸入輸出就是遠端程序的標準
輸入輸出，所以遠端的工作在本機看起來跟本機的工作一模一樣。沒有另外的 SSH 函式庫，
金鑰、代理程式與 ``~/.ssh/config`` 都照使用者平常的設定運作。
Every remote operation is an ``ssh`` process started on this machine. Its standard
input and output are the remote process's, so a remote task looks exactly like a
local one from here. No SSH library is involved, and keys, the agent and
``~/.ssh/config`` all work the way the user already has them set up.

一律以 ``BatchMode`` 執行：ssh 不會停下來問密碼或確認主機金鑰，連不上就是失敗，
編輯器因此不會卡在一個看不到的提示上。這表示要先設定好金鑰登入。
``BatchMode`` is always on: ssh never stops to ask for a password or to confirm
a host key, a connection that cannot be made simply fails, and the editor never
hangs on a prompt nobody can see. Key-based login therefore has to be set up
beforehand.
"""
from __future__ import annotations

import json
import re
import shlex
import socket
import threading
from collections.abc import Sequence
from dataclasses import dataclass

from je_editor.adapters.remote.remote_helper import (
    HELPER_SOURCE, OP_INTERPRETERS, OP_LIST, OP_PROBE, OP_READ, OP_RUN, OP_STAT, OP_WRITE,
    REMOTE_PYTHON_CANDIDATES
)
from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import OutputStream, TaskHandle, TaskRunner, TaskSpec
from je_editor.core.remote.remote_session import (
    RemoteEntry, RemoteInterpreter, RemoteState
)
from je_editor.utils.exception.exceptions import JEditorServiceException
from je_editor.utils.logging.loggin_instance import jeditor_logger

SCHEME = "ssh"
DEFAULT_SSH_PROGRAM = ("ssh",)
# 不問任何問題；十秒連不上就算失敗 / Ask nothing; a connection not made within ten seconds has failed
DEFAULT_OPTIONS = ("-o", "BatchMode=yes", "-o", "ConnectTimeout=10")
# 一個遠端操作最多等幾秒 / Seconds one remote operation may take
OPERATION_TIMEOUT_SECONDS = 60.0
MAX_PORT = 65535
# 使用者名稱與主機名稱只收這些字元：開頭不能是 "-"，否則會被 ssh 當成選項
# User and host names take these characters only, and may not start with "-",
# which ssh would read as an option
_NAME = r"[A-Za-z0-9_][A-Za-z0-9._-]*"
_AUTHORITY = re.compile(rf"^(?:(?P<user>{_NAME})@)?(?P<host>{_NAME}|\[[0-9A-Fa-f:]+\])(?::(?P<port>\d+))?$")


@dataclass(frozen=True)
class SshTarget:
    """
    要連到哪一台機器
    The machine to connect to.

    :param host: 主機名稱或位址 / the host name or address
    :param user: 使用者名稱，空字串表示讓 ssh 自己決定 / the user name, empty to let ssh decide
    :param port: 連接埠，零表示讓 ssh 自己決定 / the port, zero to let ssh decide
    """

    host: str
    user: str = ""
    port: int = 0

    @property
    def destination(self) -> str:
        """給 ssh 的目的地 / The destination as ssh takes it."""
        return f"{self.user}@{self.host}" if self.user else self.host


def parse_authority(authority: str) -> SshTarget:
    """
    解析 URI 裡的 authority
    Parse the authority of a URI.

    :param authority: ``[使用者@]主機[:連接埠]`` / ``[user@]host[:port]``
    :return: 要連到的機器 / the machine to connect to
    :raises JEditorServiceException: 格式不對，或裡面有不允許的字元
        when it is malformed or holds a character that is not allowed
    """
    match = _AUTHORITY.match(authority or "")
    if match is None:
        raise JEditorServiceException(f"Not a usable remote host: {authority!r}")
    port = int(match.group("port") or 0)
    if port > MAX_PORT:
        raise JEditorServiceException(f"Not a usable remote port: {port}")
    return SshTarget(match.group("host").strip("[]"), match.group("user") or "", port)


@dataclass(frozen=True)
class Completed:
    """
    一個遠端操作跑完的結果
    What a remote operation ended with.

    :param exit_code: 結束代碼，逾時為 ``None`` / the exit code, ``None`` on a timeout
    :param output: 標準輸出 / what it wrote to standard output
    :param errors: 標準錯誤 / what it wrote to standard error
    """

    exit_code: int | None
    output: bytes
    errors: bytes


def run_to_completion(task: TaskHandle, data: bytes = b"",
                      timeout: float = OPERATION_TIMEOUT_SECONDS) -> Completed:
    """
    啟動一個工作、把資料餵給它、等它結束
    Start a task, feed it its input and wait for it to end.

    :param task: 還沒啟動的工作，必須是 ``binary`` 的 / a task not started yet, which has to be ``binary``
    :param data: 要寫到它標準輸入的資料 / the data for its standard input
    :param timeout: 最多等幾秒 / seconds to wait at most
    :return: 結束代碼與輸出；啟動不了或逾時時結束代碼為 ``None``
        the exit code and the output; the exit code is ``None`` when it could not start or timed out
    """
    output: list[bytes] = []
    errors: list[bytes] = []
    done = threading.Event()
    task.output.subscribe(
        lambda stream, chunk: (output if stream is OutputStream.STDOUT else errors).append(chunk))
    task.finished.subscribe(lambda _code: done.set())
    if not task.start():
        return Completed(None, b"", b"could not start")
    if data:
        task.write(data)
    task.close_input()
    if not done.wait(timeout):
        task.cancel()
        return Completed(None, b"".join(output), b"timed out")
    return Completed(task.exit_code(), b"".join(output), b"".join(errors))


class SshCommand:
    """
    組出「在遠端執行這件事」的本機指令
    Builds the local command that does something on the remote side.
    """

    def __init__(self, target: SshTarget, program: Sequence[str] = DEFAULT_SSH_PROGRAM,
                 options: Sequence[str] = DEFAULT_OPTIONS) -> None:
        """
        :param target: 要連到的機器 / the machine to connect to
        :param program: ssh 程式本身 / the ssh program itself
        :param options: 每次都加上的選項 / options added every time
        """
        self._target = target
        self._program = tuple(program)
        self._options = tuple(options)

    def _prefix(self, extra: Sequence[str] = ()) -> tuple[str, ...]:
        """ssh 與它的選項，到目的地為止 / ssh and its options, up to the destination."""
        port = ("-p", str(self._target.port)) if self._target.port else ()
        # "--" 之後的東西一律不是選項，目的地因此不可能被當成選項
        # Nothing after "--" is an option, so the destination can never be taken for one
        return (*self._program, *self._options, *port, *extra, "--", self._target.destination)

    def remote(self, arguments: Sequence[str]) -> tuple[str, ...]:
        """
        在遠端執行一個引數清單
        Run an argument list on the remote side.

        ssh 會把指令交給遠端的 shell，所以每個引數都先加上引號。
        ssh hands the command to the remote shell, so every argument is quoted first.

        :param arguments: 遠端的程式與它的引數 / the remote program and its arguments
        :return: 本機要執行的指令 / the command to run on this machine
        """
        return (*self._prefix(), shlex.join(arguments))

    def forward(self, local_port: int, remote_host: str, remote_port: int) -> tuple[str, ...]:
        """
        只轉送連接埠、不執行任何指令
        Forward a port and run no command.

        :param local_port: 本機的連接埠 / the port on this machine
        :param remote_host: 從遠端機器看出去的主機 / the host as seen from the remote machine
        :param remote_port: 遠端的連接埠 / the port on the remote side
        :return: 本機要執行的指令 / the command to run on this machine
        """
        spec = f"127.0.0.1:{local_port}:{remote_host}:{remote_port}"
        return self._prefix(("-N", "-o", "ExitOnForwardFailure=yes", "-L", spec))


class SshFileSystem:
    """
    透過遠端的幫手程式讀寫檔案
    Files read and written through the helper on the remote side.
    """

    def __init__(self, session: SshRemoteSession) -> None:
        """
        :param session: 檔案系統所屬的工作階段 / the session this file system belongs to
        """
        self._session = session

    def read_bytes(self, path: str) -> bytes:
        """
        讀出一個檔案的內容
        Read a file's content.

        :param path: 檔案路徑 / the file's path
        :return: 內容 / the content
        :raises JEditorServiceException: 讀不到 / when it cannot be read
        """
        return self._session.helper(OP_READ, [path])

    def write_bytes(self, path: str, data: bytes) -> None:
        """
        寫入一個檔案，原本的內容整個換掉
        Write a file, replacing whatever it held.

        :param path: 檔案路徑 / the file's path
        :param data: 要寫入的內容 / the content to write
        :raises JEditorServiceException: 寫不進去 / when it cannot be written
        """
        self._session.helper(OP_WRITE, [path], data)

    def list_directory(self, path: str) -> tuple[RemoteEntry, ...]:
        """
        列出一個目錄裡的項目
        List the entries of a directory.

        :param path: 目錄路徑 / the directory's path
        :return: 項目，目錄在前、依名稱排序 / the entries, directories first, sorted by name
        :raises JEditorServiceException: 列不出來 / when it cannot be listed
        """
        return tuple(_entry(item) for item in self._session.helper_json(OP_LIST, [path]))

    def stat(self, path: str) -> RemoteEntry | None:
        """
        查詢一個路徑
        Look a path up.

        :param path: 路徑 / the path
        :return: 那個項目，不存在時為 ``None`` / the entry, or ``None`` when there is none
        :raises JEditorServiceException: 問不到遠端 / when the remote cannot be asked
        """
        found = self._session.helper_json(OP_STAT, [path])
        return None if found is None else _entry(found)


def _entry(item: dict) -> RemoteEntry:
    """把幫手程式回報的一筆變成 ``RemoteEntry`` / Turn one item the helper reported into a ``RemoteEntry``."""
    return RemoteEntry(str(item.get("name", "")), str(item.get("path", "")),
                       item.get("is_directory") is True, int(item.get("size") or 0),
                       float(item.get("modified") or 0.0))


class SshTaskRunner:
    """
    在遠端機器上執行工作
    Tasks that run on the remote machine.
    """

    def __init__(self, session: SshRemoteSession) -> None:
        """
        :param session: 執行器所屬的工作階段 / the session this runner belongs to
        """
        self._session = session

    def create(self, spec: TaskSpec) -> TaskHandle:
        """
        準備一個遠端的工作，但還不啟動
        Prepare a remote task without starting it.

        :param spec: 要在遠端執行什麼；工作目錄與環境變數都是遠端的
            what to run remotely; the working directory and environment are the remote ones
        :return: 這個工作的把手 / the handle for the task
        """
        environment = [f"{key}={value}" for key, value in spec.environment.items()]
        arguments = [spec.working_directory, str(len(environment)), *environment, *spec.command]
        return self._session.helper_task(OP_RUN, arguments, spec.name, spec.binary)

    def shutdown(self) -> None:
        """遠端的工作由本機的執行器一起結束 / Remote tasks are stopped along with the local runner's."""


class SshPortForward:
    """
    一條以 ssh 轉送的連接埠
    One port forwarded by ssh.
    """

    def __init__(self, task: TaskHandle, local_port: int, remote_port: int) -> None:
        """
        :param task: 負責轉送的 ssh 程序 / the ssh process doing the forwarding
        :param local_port: 本機這一端的連接埠 / the port on this machine
        :param remote_port: 遠端那一端的連接埠 / the port on the remote side
        """
        self._task = task
        self._local_port = local_port
        self._remote_port = remote_port

    @property
    def local_port(self) -> int:
        """本機這一端的連接埠 / The port on this machine."""
        return self._local_port

    @property
    def remote_port(self) -> int:
        """遠端那一端的連接埠 / The port on the remote side."""
        return self._remote_port

    def is_open(self) -> bool:
        """
        是否還在轉送
        Whether it is still forwarding.

        :return: 還在轉送時為 ``True`` / ``True`` while it forwards
        """
        return self._task.exit_code() is None

    def close(self) -> None:
        """停止轉送 / Stop forwarding."""
        self._task.cancel()


class SshRemoteSession:
    """
    一條以 ssh 連到遠端機器的工作階段
    A session connected to a remote machine through ssh.
    """

    def __init__(self, authority: str, runner: TaskRunner,
                 program: Sequence[str] = DEFAULT_SSH_PROGRAM,
                 options: Sequence[str] = DEFAULT_OPTIONS) -> None:
        """
        :param authority: ``[使用者@]主機[:連接埠]`` / ``[user@]host[:port]``
        :param runner: 用來啟動 ssh 的本機執行器 / the local runner ssh is started with
        :param program: ssh 程式本身 / the ssh program itself
        :param options: 每次都加上的選項 / options added every time
        :raises JEditorServiceException: authority 不能用 / when the authority is not usable
        """
        self._authority = authority
        self._runner = runner
        self._command = SshCommand(parse_authority(authority), program, options)
        self._state_changed = EventHook()
        self._state = RemoteState.DISCONNECTED
        self._last_error = ""
        self._python = ""
        self._forwards: list[SshPortForward] = []

    @property
    def authority(self) -> str:
        """連到哪裡 / Where it connects to."""
        return self._authority

    @property
    def state_changed(self) -> EventHook:
        """狀態改變後發出，引數是新的狀態 / Fired with the new state."""
        return self._state_changed

    def state(self) -> RemoteState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """
        return self._state

    def last_error(self) -> str:
        """
        最近一次連線失敗的原因
        Why the last attempt to connect failed.

        :return: 說明，沒有失敗時為空字串 / the reason, empty when nothing failed
        """
        return self._last_error

    def connect(self) -> bool:
        """
        建立連線：確認連得上，並找出遠端的 Python
        Open the connection: check the machine can be reached and find its Python.

        :return: 有連上時為 ``True`` / ``True`` when it connected
        """
        return self._probe(RemoteState.CONNECTING)

    def reconnect(self) -> bool:
        """
        連線斷了之後再連一次
        Connect again after the connection was lost.

        :return: 有連上時為 ``True`` / ``True`` when it connected
        """
        return self._probe(RemoteState.RECONNECTING)

    def disconnect(self) -> None:
        """
        中斷連線並停止所有轉送
        Close the connection and stop every forward.
        """
        forwards, self._forwards = self._forwards, []
        for forward in forwards:
            forward.close()
        self._python = ""
        self._set_state(RemoteState.DISCONNECTED)

    def task_runner(self) -> SshTaskRunner:
        """
        取得在遠端機器上執行工作的地方
        Somewhere tasks run on the remote machine.

        :return: 遠端的工作執行器 / the remote task runner
        """
        return SshTaskRunner(self)

    def file_system(self) -> SshFileSystem:
        """
        取得遠端機器的檔案系統
        The remote machine's file system.

        :return: 檔案系統 / the file system
        """
        return SshFileSystem(self)

    def forward_port(self, remote_port: int, remote_host: str = "127.0.0.1",
                     local_port: int = 0) -> SshPortForward:
        """
        把遠端的一個連接埠轉送到本機
        Forward a port of the remote side to this machine.

        :param remote_port: 遠端的連接埠 / the port on the remote side
        :param remote_host: 從遠端機器看出去的主機 / the host as seen from the remote machine
        :param local_port: 本機要用的連接埠，零表示挑一個空的 / the local port, zero to pick a free one
        :return: 轉送的把手 / the handle of the forward
        :raises JEditorServiceException: 連接埠或主機不能用，或轉送啟動不了
            when a port or the host is not usable, or the forward cannot start
        """
        if not 0 < remote_port <= MAX_PORT or not 0 <= local_port <= MAX_PORT:
            raise JEditorServiceException(f"Not a usable port to forward: {remote_port}")
        if re.fullmatch(_NAME, remote_host) is None:
            raise JEditorServiceException(f"Not a usable host to forward to: {remote_host!r}")
        chosen = local_port or _free_local_port()
        task = self._runner.create(TaskSpec(
            self._command.forward(chosen, remote_host, remote_port), name="port forward", binary=True))
        if not task.start():
            raise JEditorServiceException(f"Could not forward port {remote_port} of {self._authority}")
        forward = SshPortForward(task, chosen, remote_port)
        self._forwards.append(forward)
        return forward

    def interpreters(self, root: str = "") -> tuple[RemoteInterpreter, ...]:
        """
        找出遠端機器上可以用的 Python 直譯器
        Find the Python interpreters available on the remote machine.

        :param root: 專案目錄；給了就連它底下的虛擬環境一起找
            a project directory, whose virtual environments are looked at too when given
        :return: 找到的直譯器，專案自己的在前 / the interpreters found, the project's own first
        :raises JEditorServiceException: 問不到遠端 / when the remote cannot be asked
        """
        return tuple(RemoteInterpreter(str(item.get("path", "")), str(item.get("version", "")))
                     for item in self.helper_json(OP_INTERPRETERS, [root]))

    def helper_task(self, operation: str, arguments: Sequence[str], name: str = "",
                    binary: bool = True) -> TaskHandle:
        """
        準備一個請遠端幫手程式做事的工作
        Prepare a task that has the remote helper do something.

        :param operation: 操作名稱 / the operation's name
        :param arguments: 操作的引數 / the operation's arguments
        :param name: 給使用者看的名稱 / the name to show the user
        :param binary: 輸出是否以位元組送出 / whether output is delivered as bytes
        :return: 還沒啟動的工作 / a task that has not started
        :raises JEditorServiceException: 還沒連線 / when not connected
        """
        if not self._python:
            raise JEditorServiceException(f"Not connected to {self._authority}")
        remote = [self._python, "-c", HELPER_SOURCE, operation, *arguments]
        return self._runner.create(TaskSpec(self._command.remote(remote), name=name or operation,
                                            binary=binary))

    def helper(self, operation: str, arguments: Sequence[str], data: bytes = b"") -> bytes:
        """
        請遠端幫手程式做一件事，並等它做完
        Have the remote helper do one thing, and wait for it.

        :param operation: 操作名稱 / the operation's name
        :param arguments: 操作的引數 / the operation's arguments
        :param data: 要交給它的資料 / the data to hand it
        :return: 它的輸出 / its output
        :raises JEditorServiceException: 還沒連線，或那件事做不到
            when not connected, or when it could not be done
        """
        done = run_to_completion(self.helper_task(operation, arguments), data)
        if done.exit_code != 0:
            reason = done.errors.decode("utf-8", "replace").strip() or "no answer"
            raise JEditorServiceException(f"{self._authority}: {operation} failed: {reason}")
        return done.output

    def helper_json(self, operation: str, arguments: Sequence[str]) -> object:
        """
        請遠端幫手程式做一件回覆 JSON 的事
        Have the remote helper do something that answers in JSON.

        :param operation: 操作名稱 / the operation's name
        :param arguments: 操作的引數 / the operation's arguments
        :return: 解析後的回覆 / the parsed answer
        :raises JEditorServiceException: 做不到，或回覆不是 JSON
            when it could not be done, or the answer is not JSON
        """
        output = self.helper(operation, arguments)
        try:
            return json.loads(output.decode("utf-8"))
        except ValueError as error:
            raise JEditorServiceException(
                f"{self._authority}: {operation} gave an answer that is not JSON") from error

    def _probe(self, while_state: RemoteState) -> bool:
        """試著連線，並找出遠端可以用的 Python / Try to connect and find a usable Python on the remote side."""
        self._set_state(while_state)
        reason = "no Python was found on the remote machine"
        for candidate in REMOTE_PYTHON_CANDIDATES:
            remote = [candidate, "-c", HELPER_SOURCE, OP_PROBE]
            done = run_to_completion(self._runner.create(
                TaskSpec(self._command.remote(remote), name="connect", binary=True)))
            if done.exit_code == 0:
                self._python = candidate
                self._last_error = ""
                self._set_state(RemoteState.CONNECTED)
                return True
            reason = done.errors.decode("utf-8", "replace").strip() or reason
        self._python = ""
        self._last_error = reason
        jeditor_logger.info("could not connect to %s: %s", self._authority, reason)
        self._set_state(RemoteState.FAILED)
        return False

    def _set_state(self, state: RemoteState) -> None:
        """換狀態，真的變了才通知 / Change state, announcing it only when it really changed."""
        if state is not self._state:
            self._state = state
            self._state_changed.emit(state)


def _free_local_port() -> int:
    """向作業系統要一個目前沒人用的本機連接埠 / Ask the system for a local port nobody is using right now."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]

"""
在本機執行工作
Tasks that run on this machine.

``TaskRunner`` 的本機實作：以引數清單啟動子程序（從不經過 shell），各用一條執行緒
讀標準輸出與標準錯誤，讀到什麼就通知訂閱者。除錯轉接器靠它啟動；之後的遠端執行
會是同一個介面的另一個實作。
The local implementation of ``TaskRunner``: it starts a child process from an
argument list, never through a shell, reads standard output and standard error
on a thread each, and tells subscribers what was read. Debug adapters are
started through it, and remote execution will be another implementation of the
same interface.
"""
from __future__ import annotations

import os
import subprocess  # nosec B404 - 執行工作就是它的用途；一律以引數清單啟動，shell=False
import threading
from typing import IO

from je_editor.core.events.event_hook import EventHook
from je_editor.core.process.task_service import OutputStream, TaskSpec, TaskState
from je_editor.utils.logging.loggin_instance import jeditor_logger

_ENCODING = "utf-8"
# 一次最多讀這麼多位元組；read1 有多少給多少，不會等到湊滿
# At most this many bytes per read; read1 returns what there is without waiting to fill it
_READ_SIZE = 65536
# 取消之後等程序結束的秒數，超過就強制結束
# Seconds to wait for the process after a cancel before it is killed
_STOP_TIMEOUT = 3.0


class LocalTask:
    """
    本機的一個工作：一個子程序與讀它輸出的執行緒
    One local task: a child process and the threads reading its output.
    """

    def __init__(self, spec: TaskSpec) -> None:
        """
        :param spec: 要執行什麼 / what to run
        """
        self._spec = spec
        self._output = EventHook()
        self._finished = EventHook()
        self._state = TaskState.PENDING
        self._process: subprocess.Popen | None = None
        self._exit_code: int | None = None
        self._lock = threading.Lock()
        self._readers: list[threading.Thread] = []
        # 結束代碼已經記下、也通知過訂閱者之後才設起來
        # Set once the exit code is recorded and the subscribers have been told
        self._done = threading.Event()

    @property
    def spec(self) -> TaskSpec:
        """這個工作要執行什麼 / What this task runs."""
        return self._spec

    @property
    def output(self) -> EventHook:
        """有輸出時發出，引數是串流與內容 / Fired with the stream and what was read."""
        return self._output

    @property
    def finished(self) -> EventHook:
        """結束後發出，引數是結束代碼 / Fired with the exit code once it ends."""
        return self._finished

    def state(self) -> TaskState:
        """
        目前的狀態
        The current state.

        :return: 狀態 / the state
        """
        return self._state

    def exit_code(self) -> int | None:
        """
        結束代碼
        The exit code.

        :return: 結束代碼，還沒結束時為 ``None`` / the code, or ``None`` while it runs
        """
        return self._exit_code

    def start(self) -> bool:
        """
        啟動程序
        Start the process.

        :return: 有啟動時為 ``True``；已經啟動過或啟動失敗時為 ``False``
            ``True`` when it started, ``False`` when it already had or could not
        """
        with self._lock:
            if self._state is not TaskState.PENDING:
                return False
            try:
                # 指令來自 TaskSpec：建立時就確認過是非空字串組成的清單，而且從不經過 shell
                # The command comes from a TaskSpec, checked on creation to be a list of
                # non-empty strings, and never goes through a shell
                self._process = subprocess.Popen(  # nosemgrep  # noqa: S603  # nosec B603
                    list(self._spec.command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, cwd=self._spec.working_directory or None,
                    env={**os.environ, **self._spec.environment}, shell=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            except OSError as error:
                jeditor_logger.warning("task %s could not start: %s", self._spec.command[0], error)
                self._state = TaskState.FAILED_TO_START
                return False
            self._state = TaskState.RUNNING
        self._readers = [
            self._reader(self._process.stdout, OutputStream.STDOUT),
            self._reader(self._process.stderr, OutputStream.STDERR),
        ]
        threading.Thread(target=self._wait, name="LocalTask-wait", daemon=True).start()
        return True

    def write(self, text: str | bytes) -> bool:
        """
        寫到程序的標準輸入
        Write to the process's standard input.

        :param text: 要寫入的文字或位元組 / the text or bytes to write
        :return: 有寫入時為 ``True`` / ``True`` when it was written
        """
        process = self._process
        if process is None or process.stdin is None or self._state is not TaskState.RUNNING:
            return False
        data = text.encode(_ENCODING) if isinstance(text, str) else text
        try:
            with self._lock:
                process.stdin.write(data)
                process.stdin.flush()
        except (OSError, ValueError) as error:
            # 程序已經結束、管線關了 / The process is gone and the pipe is closed
            jeditor_logger.debug("write to task %s failed: %s", self._spec.command[0], error)
            return False
        return True

    def cancel(self) -> None:
        """
        結束程序
        Stop the process.

        先請它結束，等不到再強制結束。
        It is asked to end first, and killed when it does not.
        """
        process = self._process
        if process is None or process.poll() is not None:
            return
        self._state = TaskState.CANCELLED
        process.terminate()
        try:
            process.wait(_STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()

    def wait(self, timeout: float | None = None) -> bool:
        """
        等到程序結束、輸出讀完、結束代碼也通知出去
        Wait until the process has ended, its output has been read and its exit
        code has been announced.

        :param timeout: 最多等幾秒，``None`` 表示一直等 / seconds to wait at most, ``None`` to wait for ever
        :return: 結束了為 ``True``；沒有啟動過的工作也算結束
            ``True`` once it has ended; a task that never started counts as ended
        """
        if self._process is None:
            return True
        return self._done.wait(timeout)

    def _reader(self, pipe: IO[bytes] | None, stream: OutputStream) -> threading.Thread:
        """開一條執行緒讀一個串流 / Start a thread reading one stream."""
        thread = threading.Thread(target=self._read, args=(pipe, stream),
                                  name=f"LocalTask-{stream.value}", daemon=True)
        thread.start()
        return thread

    def _read(self, pipe: IO[bytes] | None, stream: OutputStream) -> None:
        """把一個串流讀到結束，讀到什麼就通知什麼 / Read a stream to its end, passing on what is read."""
        if pipe is None:
            return
        while True:
            try:
                data = pipe.read1(_READ_SIZE)
            except (OSError, ValueError):
                break
            if not data:
                break
            self._output.emit(stream, data if self._spec.binary else data.decode(_ENCODING, "replace"))
        pipe.close()

    def _wait(self) -> None:
        """等程序結束，再通知結束代碼 / Wait for the process to end, then announce its exit code."""
        process = self._process
        if process is None:
            return
        code = process.wait()
        for reader in self._readers:
            reader.join()
        if process.stdin is not None:
            try:
                process.stdin.close()
            except OSError as error:
                jeditor_logger.debug("closing the input of task %s: %s", self._spec.command[0], error)
        self._exit_code = code
        if self._state is TaskState.RUNNING:
            self._state = TaskState.FINISHED
        self._finished.emit(code)
        self._done.set()


class LocalTaskRunner:
    """
    在本機執行工作的地方
    Somewhere tasks run on this machine.
    """

    def __init__(self) -> None:
        self._tasks: list[LocalTask] = []
        self._lock = threading.Lock()

    def create(self, spec: TaskSpec) -> LocalTask:
        """
        準備一個工作，但還不啟動
        Prepare a task without starting it.

        :param spec: 要執行什麼 / what to run
        :return: 這個工作的把手 / the handle for the task
        """
        task = LocalTask(spec)
        with self._lock:
            # 順手丟掉已經結束的，清單才不會一直長 / Drop the ones that have ended so the list does not grow for ever
            self._tasks = [held for held in self._tasks if held.exit_code() is None]
            self._tasks.append(task)
        return task

    def shutdown(self) -> None:
        """
        結束所有還在執行的工作
        Stop every task that is still running.
        """
        with self._lock:
            tasks, self._tasks = self._tasks, []
        for task in tasks:
            task.cancel()

import time
from queue import Queue
from typing import Dict

from watchdog.events import FileSystemEventHandler

from je_editor.code_scan.ruff_thread import RuffThread


class RuffPythonFileChangeHandler(FileSystemEventHandler):
    """
    File system event handler that runs Ruff when Python files are modified.
    當 Python 檔案被修改時，自動觸發 Ruff 檢查。
    """

    def __init__(self, ruff_commands: list = None, debounce_interval: float = 1.0):
        """
        :param ruff_commands: Ruff command list, e.g. ["ruff", "check"]
        :param debounce_interval: Minimum interval (seconds) between re-runs for the same file
                                  同一檔案觸發 Ruff 的最小間隔秒數
        """
        super().__init__()
        self.ruff_commands = ruff_commands or ["ruff", "check"]
        self.stdout_queue: Queue = Queue()
        self.stderr_queue: Queue = Queue()
        self.ruff_threads_dict: Dict[str, RuffThread] = {}
        self.last_run_time: Dict[str, float] = {}
        self.debounce_interval = debounce_interval

    def _start_new_thread(self, file_path: str):
        """Helper to start a new Ruff thread for a given file."""
        ruff_thread = RuffThread(self.ruff_commands, self.stdout_queue, self.stderr_queue)
        self.ruff_threads_dict[file_path] = ruff_thread
        self.last_run_time[file_path] = time.time()
        ruff_thread.start()

    def on_modified(self, event):
        """Triggered when a file is modified."""
        if event.is_directory:
            return

        if not event.src_path.endswith(".py"):
            return

        now = time.time()
        last_time = self.last_run_time.get(event.src_path, 0)

        # Debounce: skip if last run was too recent
        if now - last_time < self.debounce_interval:
            return

        ruff_thread = self.ruff_threads_dict.get(event.src_path)

        if ruff_thread is None or not ruff_thread.is_alive():
            self._start_new_thread(event.src_path)
        # else: thread still running, skip
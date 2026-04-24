import subprocess  # nosec B404 - 呼叫 ruff 時以引數清單傳遞，未使用 shell
import threading
import time
from queue import Queue


class RuffThread(threading.Thread):
    """
    A thread class to run Ruff (a Python linter/formatter) as a subprocess.
    使用子執行緒執行 Ruff (Python 程式碼檢查/格式化工具)。
    """

    def __init__(self, ruff_commands: list, std_queue: Queue, stderr_queue: Queue) -> None:
        """
        Initialize the RuffThread.
        初始化 RuffThread。

        :param ruff_commands: list of commands to run Ruff, e.g. ["ruff", "check"]
                              要執行的 Ruff 指令，例如 ["ruff", "check"]
        :param std_queue: queue to store standard output
                          用來存放標準輸出的佇列
        :param stderr_queue: queue to store error output
                             用來存放錯誤輸出的佇列
        """
        super().__init__()
        if ruff_commands is None:
            self.ruff_commands = ["ruff", "check"]
        else:
            self.ruff_commands = ruff_commands

        self.ruff_process = None
        self.std_queue = std_queue
        self.stderr_queue = stderr_queue

    def run(self) -> None:
        """
        Run the Ruff process in a separate thread.
        在子執行緒中執行 Ruff 程式。
        """
        # 啟動子程序，捕捉 stdout 與 stderr
        # 指令由開發者建立為引數清單，未使用 shell
        # Command is a dev-provided argument list; no shell interpretation
        self.ruff_process = subprocess.Popen(  # nosemgrep  # noqa: S603  # nosec B603
            self.ruff_commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # 等待子程序結束
        while self.ruff_process.poll() is None:
            time.sleep(1)

        # 子程序結束後，讀取 stdout 與 stderr
        for line in self.ruff_process.stdout:
            self.std_queue.put(line.strip())

        for line in self.ruff_process.stderr:
            self.stderr_queue.put(line.strip())

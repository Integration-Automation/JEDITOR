import subprocess
import threading
import time
from queue import Queue


class RuffThread(threading.Thread):

    def __init__(self, ruff_commands: list, std_queue: Queue, stderr_queue: Queue):
        super().__init__()
        if ruff_commands is None:
            self.ruff_commands = ["ruff", "check"]
        else:
            self.ruff_commands = ruff_commands
        self.ruff_process = None
        self.std_queue = std_queue
        self.stderr_queue = stderr_queue

    def run(self):
        self.ruff_process = subprocess.Popen(
            self.ruff_commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        while self.ruff_process.poll() is None:
            time.sleep(1)
        else:
            for line in self.ruff_process.stdout:
                print(line.strip())
            for line in self.ruff_process.stderr:
                print(line.strip())




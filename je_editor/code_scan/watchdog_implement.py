from queue import Queue

from watchdog.events import FileSystemEventHandler

from je_editor.code_scan.ruff_thread import RuffThread


class RuffPythonFileChangeHandler(FileSystemEventHandler):

    def __init__(self, ruff_commands: list = None):
        super(RuffPythonFileChangeHandler, self).__init__()
        self.ruff_commands = ruff_commands
        self.stdout_queue = Queue()
        self.stderr_queue = Queue()
        self.ruff_threads_dict = dict()

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".py"):
            if self.ruff_threads_dict.get(event.src_path) is None:
                ruff_thread = RuffThread(self.ruff_commands, self.stdout_queue, self.stderr_queue)
                self.ruff_threads_dict.update({event.src_path: ruff_thread})
                ruff_thread.start()
            else:
                ruff_thread = self.ruff_threads_dict.get(event.src_path)
                if not ruff_thread.is_alive():
                    ruff_thread = RuffThread(self.ruff_commands, self.stdout_queue, self.stderr_queue)
                    self.ruff_threads_dict.update({event.src_path: ruff_thread})
                    ruff_thread.start()
                else:
                    pass



import threading
import time

from watchdog.observers import Observer

from je_editor.code_scan.watchdog_implement import RuffPythonFileChangeHandler


class WatchdogThread(threading.Thread):

    def __init__(self, check_path: str):
        super().__init__()
        self.check_path = check_path
        self.ruff_handler = RuffPythonFileChangeHandler()
        self.running = True

    def run(self):
        observer = Observer()
        observer.schedule(self.ruff_handler, str(self.check_path), recursive=True)
        observer.start()
        try:
            while self.running:
                time.sleep(1)
        finally:
            observer.stop()


if __name__ == '__main__':
    watchdog_thread = WatchdogThread("")
    watchdog_thread.start()
    while True:
        time.sleep(1)


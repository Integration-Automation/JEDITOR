import threading
import time
import sys
from pathlib import Path

from watchdog.observers import Observer

from je_editor.code_scan.watchdog_implement import RuffPythonFileChangeHandler


class WatchdogThread(threading.Thread):
    """
    A thread that runs a watchdog observer to monitor file changes.
    使用 watchdog 監控檔案變化的執行緒。
    """

    def __init__(self, check_path: str):
        """
        :param check_path: Path to monitor (directory or file)
                           要監控的路徑（資料夾或檔案）
        """
        super().__init__(daemon=True)  # 設為 daemon，主程式結束時自動退出
        self.check_path = Path(check_path).resolve()
        self.ruff_handler = RuffPythonFileChangeHandler()
        self.running = True
        self.observer = Observer()

    def run(self):
        """Start the watchdog observer loop."""
        if not self.check_path.exists():
            print(f"[Error] Path does not exist: {self.check_path}", file=sys.stderr)
            return

        # 設定監控
        self.observer.schedule(self.ruff_handler, str(self.check_path), recursive=True)
        self.observer.start()
        print(f"[Watchdog] Monitoring started on {self.check_path}")

        try:
            while self.running:
                time.sleep(1)
                # 這裡可以加上 queue 輸出處理
                self._process_ruff_output()
        except KeyboardInterrupt:
            print("[Watchdog] Interrupted by user")
        finally:
            self.observer.stop()
            self.observer.join()
            print("[Watchdog] Monitoring stopped")

    def stop(self):
        """Stop the watchdog thread safely."""
        self.running = False

    def _process_ruff_output(self):
        """Process stdout/stderr queues from Ruff threads."""
        while not self.ruff_handler.stdout_queue.empty():
            line = self.ruff_handler.stdout_queue.get()
            print(f"[Ruff STDOUT] {line}")

        while not self.ruff_handler.stderr_queue.empty():
            line = self.ruff_handler.stderr_queue.get()
            print(f"[Ruff STDERR] {line}", file=sys.stderr)


if __name__ == '__main__':
    # 預設監控當前目錄
    path_to_watch = "."
    watchdog_thread = WatchdogThread(path_to_watch)
    watchdog_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Main] Stopping watchdog...")
        watchdog_thread.stop()
        watchdog_thread.join()
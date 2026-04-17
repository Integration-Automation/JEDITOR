from __future__ import annotations

import queue
import subprocess
from threading import Thread
from typing import Union

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QTextEdit, QWidget

from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger


class BaseProcessManager:
    """
    程式/Shell 執行管理器的共用基底類別。
    Base class for ExecManager and ShellManager with shared process logic.
    """

    def __init__(
            self,
            main_window: Union[QWidget, None] = None,
            encoding: str = "utf-8",
            buffer_size: int = 1024,
    ) -> None:
        self.read_program_error_output_from_thread: Union[Thread, None] = None
        self.read_program_output_from_thread: Union[Thread, None] = None
        self.main_window = main_window
        self.code_result: Union[QTextEdit, None] = None
        self.timer: Union[QTimer, None] = None
        self._still_running: bool = True
        self.process: Union[subprocess.Popen, None] = None
        self.run_output_queue: queue.Queue = queue.Queue()
        self.run_error_queue: queue.Queue = queue.Queue()
        self.program_encoding: str = encoding
        self.program_buffer: int = buffer_size
        run_instance_manager.instance_list.append(self)

    @property
    def still_running(self) -> bool:
        return self._still_running

    @still_running.setter
    def still_running(self, value: bool) -> None:
        self._still_running = value

    def _start_reader_threads(self) -> None:
        """啟動 stdout/stderr 讀取執行緒 / Start stdout/stderr reader threads"""
        self.read_program_output_from_thread = Thread(
            target=self._read_stdout, daemon=True
        )
        self.read_program_output_from_thread.start()

        self.read_program_error_output_from_thread = Thread(
            target=self._read_stderr, daemon=True
        )
        self.read_program_error_output_from_thread.start()

    def _start_pull_timer(self, interval: int = 50) -> None:
        """啟動輸出拉取定時器 / Start output pull timer"""
        self.timer = QTimer(self.main_window)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.pull_text)
        self.timer.start()

    def pull_text(self) -> None:
        """批次從佇列中取出訊息並顯示 / Batch-drain queues and display"""
        text_cursor = self.code_result.textCursor()

        # 批次處理標準輸出 / Batch stdout
        stdout_parts = []
        try:
            while not self.run_output_queue.empty():
                msg = str(self.run_output_queue.get_nowait()).strip()
                if msg:
                    stdout_parts.append(msg)
        except queue.Empty:
            pass
        if stdout_parts:
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText("\n".join(stdout_parts), text_format)
            text_cursor.insertBlock()

        # 批次處理錯誤輸出 / Batch stderr
        stderr_parts = []
        try:
            while not self.run_error_queue.empty():
                msg = str(self.run_error_queue.get_nowait()).strip()
                if msg:
                    stderr_parts.append(msg)
        except queue.Empty:
            pass
        if stderr_parts:
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("error_output_color"))
            text_cursor.insertText("\n".join(stderr_parts), text_format)
            text_cursor.insertBlock()

        # 檢查子程序是否結束 / Check if process finished
        if self.process is not None:
            if self.process.returncode is not None:
                self._on_process_finished()
            elif self.still_running:
                self.process.poll()

    def _on_process_finished(self) -> None:
        """子程序結束時呼叫 (子類別覆寫) / Called when process finishes (override in subclass)"""
        pass

    def exit_program(self) -> None:
        """結束程式：清理執行緒、佇列與子程序 / Exit: clean threads, queues, and process"""
        jeditor_logger.info(f"{self.__class__.__name__} exit_program")
        self.still_running = False

        # 在背景清理執行緒與子程序，避免阻塞主執行緒
        # Clean up threads and process in background to avoid blocking the main thread
        threads_to_join = []
        if self.read_program_output_from_thread is not None:
            threads_to_join.append(self.read_program_output_from_thread)
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            threads_to_join.append(self.read_program_error_output_from_thread)
            self.read_program_error_output_from_thread = None

        process_to_cleanup = self.process
        self.process = None

        # 清空佇列 / Clear queues
        self.print_and_clear_queue()

        # 顯示退出訊息 / Show exit message
        if process_to_cleanup is not None and self.code_result is not None:
            returncode = process_to_cleanup.returncode
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(
                f"{self._exit_message_prefix()} exit with code {returncode}",
                text_format
            )
            text_cursor.insertBlock()

        # 在背景執行緒中做 join 和 terminate / Do join and terminate in background
        if threads_to_join or process_to_cleanup is not None:
            cleanup_thread = Thread(
                target=self._cleanup_in_background,
                args=(threads_to_join, process_to_cleanup),
                daemon=True,
            )
            cleanup_thread.start()

    @staticmethod
    def _cleanup_in_background(threads: list, process: subprocess.Popen | None) -> None:
        """在背景執行清理工作 / Perform cleanup work in background"""
        for t in threads:
            try:
                t.join(timeout=2)
            except Exception:
                pass
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    process.wait(timeout=2)
                except Exception:
                    pass
            except OSError:
                pass

    def _exit_message_prefix(self) -> str:
        """退出訊息前綴 (子類別覆寫) / Exit message prefix (override in subclass)"""
        return "Process"

    def print_and_clear_queue(self) -> None:
        """清空輸出與錯誤佇列 / Clear stdout and stderr queues"""
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def _read_stdout(self) -> None:
        """從子程序 stdout 持續讀取 / Continuously read from process stdout"""
        try:
            while self.still_running:
                if self.process is None:
                    break
                data = self.process.stdout.readline(
                    self.program_buffer
                ).decode(self.program_encoding, "replace")
                if not data and (self.process is None or self.process.poll() is not None):
                    break
                if self.process:
                    self.process.stdout.flush()
                self.run_output_queue.put_nowait(data)
        except (OSError, ValueError):
            pass

    def _read_stderr(self) -> None:
        """從子程序 stderr 持續讀取 / Continuously read from process stderr"""
        try:
            while self.still_running:
                if self.process is None:
                    break
                data = self.process.stderr.readline(
                    self.program_buffer
                ).decode(self.program_encoding, "replace")
                if not data and (self.process is None or self.process.poll() is not None):
                    break
                if self.process:
                    self.process.stderr.flush()
                self.run_error_queue.put_nowait(data)
        except (OSError, ValueError):
            pass

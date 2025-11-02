from __future__ import annotations

import os
import queue
import shlex
import subprocess
import sys
from pathlib import Path
from threading import Thread
from typing import Union, Callable

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.exception.exception_tags import je_editor_init_error
from je_editor.utils.exception.exceptions import JEditorException
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.venv_check.check_venv import check_and_choose_venv


class ShellManager(object):
    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,
            shell_encoding: str = "utf-8",
            program_buffer: int = 1024,
            after_done_function: Union[None, Callable] = None
    ):
        # 初始化 ShellManager，記錄基本設定
        # Initialize ShellManager, log basic settings
        jeditor_logger.info(f"Init ShellManager "
                            f"main_window: {main_window} "
                            f"shell_encoding: {shell_encoding} "
                            f"program_buffer: {program_buffer} "
                            f"after_done_function: {after_done_function}")
        """
        :param main_window: Pyside 主視窗 / Pyside main window
        :param shell_encoding: shell 輸出編碼 / shell command output encoding
        :param program_buffer: 緩衝區大小 / buffer size
        """
        self.read_program_error_output_from_thread = None  # 錯誤輸出讀取執行緒 / thread for reading stderr
        self.read_program_output_from_thread = None  # 標準輸出讀取執行緒 / thread for reading stdout
        self.main_window: EditorWidget = main_window  # 主視窗 / main window
        self.compiler_path = None  # Python 編譯器路徑 / Python compiler path
        self.code_result: Union[QTextEdit, None] = None  # 顯示輸出結果的文字框 / QTextEdit for displaying results
        self.timer: Union[QTimer, None] = None  # 定時器 / QTimer for periodic updates
        self.still_run_shell: bool = True  # 是否仍在執行 / flag for running state
        self.process = None  # 子程序物件 / subprocess object
        self.run_output_queue: queue.Queue = queue.Queue()  # 標準輸出佇列 / stdout queue
        self.run_error_queue: queue.Queue = queue.Queue()  # 錯誤輸出佇列 / stderr queue
        self.program_encoding: str = shell_encoding  # 編碼設定 / encoding setting
        self.program_buffer: int = program_buffer  # 緩衝區大小 / buffer size
        self.after_done_function = after_done_function  # 完成後的回呼函數 / callback after done
        self.renew_path()  # 更新 Python 執行路徑 / renew Python path
        run_instance_manager.instance_list.append(self)  # 註冊到執行管理器 / register instance

    def renew_path(self) -> None:
        # 更新 Python 編譯器路徑
        # Renew Python compiler path
        jeditor_logger.info("ShellManager renew_path")
        if self.main_window.python_compiler is None:
            # 如果主視窗沒有指定 Python，則使用 venv
            # If no compiler specified, use venv
            if sys.platform in ["win32", "cygwin", "msys"]:
                venv_path = Path(os.getcwd() + "/venv/Scripts")
            else:
                venv_path = Path(os.getcwd() + "/venv/bin")
            self.compiler_path = check_and_choose_venv(venv_path)
        else:
            self.compiler_path = self.main_window.python_compiler

    def later_init(self) -> None:
        # 延遲初始化，綁定輸出視窗
        # Late initialization, bind output QTextEdit
        jeditor_logger.info("ShellManager later_init")
        if self.main_window is not None:
            self.code_result: QTextEdit = self.main_window.code_result
        else:
            raise JEditorException(je_editor_init_error)

    def exec_shell(self, shell_command: Union[str, list]) -> None:
        """
        執行 shell 指令
        Execute shell command
        :param shell_command: 要執行的指令 / command to run
        :return: 若錯誤則回傳錯誤訊息 / return error message if failed
        """
        jeditor_logger.info(f"ShellManager exec_shell, shell_command: {shell_command}")
        try:
            self.exit_program()  # 結束舊的程序 / terminate previous process
            self.code_result.setPlainText("")  # 清空輸出視窗 / clear output window
            if sys.platform in ["win32", "cygwin", "msys"]:
                args = shell_command
            else:
                args = shlex.split(shell_command)  # 非 Windows 系統需分割指令 / split command for Unix-like
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(str(args), text_format)  # 顯示執行的指令 / show executed command
            text_cursor.insertBlock()
            # 建立子程序 / create subprocess
            self.process = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=True,
            )
            self.still_run_shell = True
            # 建立讀取標準輸出的執行緒 / thread for stdout
            self.read_program_output_from_thread = Thread(
                target=self.read_program_output_from_process,
                daemon=True
            )
            self.read_program_output_from_thread.start()
            # 建立讀取錯誤輸出的執行緒 / thread for stderr
            self.read_program_error_output_from_thread = Thread(
                target=self.read_program_error_output_from_process,
                daemon=True
            )
            self.read_program_error_output_from_thread.start()
            # 啟動定時器，每 10ms 更新一次輸出 / start QTimer for updating output
            self.timer = QTimer(self.main_window)
            self.timer.setInterval(10)
            self.timer.timeout.connect(self.pull_text)
            self.timer.start()
        except Exception as error:
            # 若發生錯誤，顯示錯誤訊息並結束程序
            # If error occurs, show error message and terminate process
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("error_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    # tkinter_ui update method
    def pull_text(self) -> None:
        # 從佇列中拉取輸出與錯誤訊息，並更新到 UI
        # Pull stdout/stderr messages from queue and update UI
        jeditor_logger.info("ShellManager pull_text")
        try:
            if not self.run_output_queue.empty():
                output_message = self.run_output_queue.get_nowait()
                output_message = str(output_message).strip()
                if output_message:
                    text_cursor = self.code_result.textCursor()
                    text_format = QTextCharFormat()
                    text_format.setForeground(actually_color_dict.get("normal_output_color"))
                    text_cursor.insertText(output_message, text_format)
                    text_cursor.insertBlock()
            if not self.run_error_queue.empty():
                error_message = self.run_error_queue.get_nowait()
                error_message = str(error_message).strip()
                if error_message:
                    text_cursor = self.code_result.textCursor()
                    text_format = QTextCharFormat()
                    text_format.setForeground(actually_color_dict.get("error_output_color"))
                    text_cursor.insertText(error_message, text_format)
                    text_cursor.insertBlock()
        except queue.Empty:
            pass
        # 檢查子程序是否結束 / check if process finished
        if self.process.returncode == 0:
            self.process_run_over()
        elif self.process.returncode is not None:
            self.process_run_over()
        if self.still_run_shell:
            # 持續檢查程序狀態 / keep polling process
            self.process.poll()

    def process_run_over(self):
        # 當子程序結束時呼叫，停止計時器並清理資源
        # Called when subprocess finishes, stop timer and clean up resources
        jeditor_logger.info("ShellManager process_run_over")
        self.timer.stop()  # 停止定時器 / stop QTimer
        self.exit_program()  # 結束程序並清理 / terminate process and cleanup
        self.main_window.exec_shell = None  # 重置 main_window 的 exec_shell / reset exec_shell reference
        if self.after_done_function is not None:
            self.after_done_function()  # 執行結束後的回呼函數 / run callback if provided

    # exit program: 將執行旗標設為 False，清理執行緒、佇列與子程序
    # exit program: set running flag to False, clean threads, queues, and subprocess
    def exit_program(self) -> None:
        jeditor_logger.info("ShellManager exit_program")
        self.still_run_shell = False  # 停止讀取迴圈 / stop reading loop
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None  # 清理 stdout 執行緒 / clear stdout thread
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None  # 清理 stderr 執行緒 / clear stderr thread
        self.print_and_clear_queue()  # 清空輸出佇列 / clear output queues
        if self.process is not None:
            self.process.terminate()  # 終止子程序 / terminate subprocess
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            # 顯示退出代碼 / show exit code
            text_cursor.insertText(f"Shell command exit with code {self.process.returncode}", text_format)
            text_cursor.insertBlock()
            self.process = None  # 清空 process 物件 / reset process object

    def print_and_clear_queue(self) -> None:
        # 清空 stdout 與 stderr 佇列
        # Reset stdout and stderr queues
        jeditor_logger.info("ShellManager print_and_clear_queue")
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def read_program_output_from_process(self) -> None:
        # 從子程序讀取標準輸出並放入佇列
        # Continuously read stdout from subprocess and put into queue
        jeditor_logger.info("ShellManager read_program_output_from_process")
        while self.still_run_shell:
            program_output_data = self.process.stdout.readline(
                self.program_buffer) \
                .decode(self.program_encoding, "replace")  # 解碼輸出 / decode output
            if self.process:
                self.process.stdout.flush()  # 清空緩衝區 / flush buffer
            self.run_output_queue.put_nowait(program_output_data)  # 放入輸出佇列 / enqueue stdout

    def read_program_error_output_from_process(self) -> None:
        # 從子程序讀取錯誤輸出並放入佇列
        # Continuously read stderr from subprocess and put into queue
        jeditor_logger.info("ShellManager read_program_error_output_from_process")
        while self.still_run_shell:
            program_error_output_data = self.process.stderr.readline(
                self.program_buffer) \
                .decode(self.program_encoding, "replace")  # 解碼錯誤輸出 / decode stderr
            if self.process:
                self.process.stderr.flush()  # 清空緩衝區 / flush buffer
            self.run_error_queue.put_nowait(program_error_output_data)  # 放入錯誤佇列 / enqueue stderr

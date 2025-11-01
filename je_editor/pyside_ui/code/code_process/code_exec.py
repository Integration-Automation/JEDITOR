from __future__ import annotations  # 支援延遲型別註解 (Python 3.7+)
# Support postponed evaluation of type annotations

import queue  # 佇列，用於執行緒間傳遞訊息
import subprocess  # 建立與管理子程序 (執行外部程式)
import sys  # 系統相關資訊 (平台、參數等)
from pathlib import Path  # 處理檔案與路徑
from threading import Thread  # 執行緒，用於非同步處理
from typing import Union  # 型別提示：允許多種型別

from PySide6.QtCore import QTimer  # Qt 計時器，用於定時觸發事件
from PySide6.QtGui import QTextCharFormat  # 設定文字格式 (顏色、字型等)
from PySide6.QtWidgets import QTextEdit  # 文字編輯器元件

# 專案內部模組
from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.exception.exception_tags import je_editor_init_error
from je_editor.utils.exception.exceptions import JEditorException
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.venv_check.check_venv import check_and_choose_venv


class ExecManager(object):
    """
    程式執行管理器
    Execution manager for running code inside the editor.
    負責：
    - 建立子程序 (subprocess)
    - 讀取標準輸出與錯誤輸出
    - 將結果顯示在 QTextEdit
    - 管理計時器與執行緒
    """

    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,  # 主視窗 (可為 None)
            program_language: str = "python",  # 預設程式語言
            program_encoding: str = "utf-8",  # 預設編碼
            program_buffer: int = 1024,  # 緩衝區大小
    ):
        """
        初始化執行管理器
        Initialize ExecManager
        """
        jeditor_logger.info(f"Init ExecManager "
                            f"main_window: {main_window} "
                            f"program_language: {program_language} "
                            f"program_encoding: {program_encoding} "
                            f"program_buffer: {program_buffer}")
        # 初始化屬性
        self.read_program_error_output_from_thread = None  # 錯誤輸出讀取執行緒
        self.read_program_output_from_thread = None  # 標準輸出讀取執行緒
        self.main_window: EditorWidget = main_window  # 主視窗
        self.compiler_path = None  # 編譯器/直譯器路徑
        self.code_result: Union[QTextEdit, None] = None  # 顯示程式輸出的文字框
        self.code_result_cursor: Union[QTextEdit.textCursor, None] = None
        self.timer: Union[QTimer, None] = None  # 定時器
        self.still_run_program = True  # 程式是否仍在執行
        self.process: Union[subprocess.Popen, None] = None  # 子程序
        self.run_output_queue = queue.Queue()  # 標準輸出佇列
        self.run_error_queue = queue.Queue()  # 錯誤輸出佇列
        self.program_language = program_language
        self.program_encoding = program_encoding
        self.program_buffer = program_buffer
        self.renew_path()  # 設定 Python 直譯器路徑
        run_instance_manager.instance_list.append(self)  # 註冊到全域執行管理器

    def renew_path(self) -> None:
        """更新 Python 直譯器路徑 / Renew compiler path"""
        jeditor_logger.info("ExecManager renew_path")
        if self.main_window.python_compiler is None:
            # 如果主視窗沒有指定 Python，則使用虛擬環境
            if sys.platform in ["win32", "cygwin", "msys"]:
                venv_path = Path(str(Path.cwd()) + "/venv/Scripts")
            else:
                venv_path = Path(str(Path.cwd()) + "/venv/bin")
            self.compiler_path = check_and_choose_venv(venv_path)
        else:
            self.compiler_path = self.main_window.python_compiler

    def later_init(self) -> None:
        """延遲初始化，設定輸出區與計時器 / Setup code result area and timer"""
        jeditor_logger.info("ExecManager later_init")
        if self.main_window is not None:
            self.code_result: QTextEdit = self.main_window.code_result
            self.timer = QTimer(self.main_window)
        else:
            raise JEditorException(je_editor_init_error)

    def exec_code(self, exec_file_name, exec_prefix: Union[str, list] = None) -> None:
        """
        執行指定檔案
        Execute given file
        :param exec_file_name: 要執行的檔案名稱
        :param exec_prefix: 使用者自定義前綴 (例如 python -m)
        """
        jeditor_logger.info(f"ExecManager exec_code "
                            f"exec_file_name: {exec_file_name} "
                            f"exec_prefix: {exec_prefix}")
        try:
            self.exit_program()  # 確保先結束舊的程式
            self.code_result.setPlainText("")  # 清空輸出區
            file_path = Path(exec_file_name)
            reformat_os_file_path = str(file_path.absolute())
            exec_file = reformat_os_file_path

            # 建立執行參數
            if exec_prefix is None:
                execute_program_param = [self.compiler_path, exec_file]
            else:
                if isinstance(exec_prefix, str):
                    execute_program_param = [self.compiler_path, exec_prefix, exec_file]
                else:
                    execute_program_param = [self.compiler_path] + exec_prefix + [exec_file]

            # 非 Windows 平台需轉為字串
            if sys.platform not in ["win32", "cygwin", "msys"]:
                execute_program_param = " ".join(execute_program_param)

            # 建立子程序
            self.process = subprocess.Popen(
                execute_program_param,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            self.still_run_program = True

            # 啟動輸出讀取執行緒
            self.read_program_output_from_thread = Thread(
                target=self.read_program_output_from_process,
                daemon=True
            )
            self.read_program_output_from_thread.start()

            # 啟動錯誤讀取執行緒
            self.read_program_error_output_from_thread = Thread(
                target=self.read_program_error_output_from_process,
                daemon=True
            )
            self.read_program_error_output_from_thread.start()

            # 顯示執行的檔案路徑
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(self.compiler_path + " " + reformat_os_file_path, text_format)
            text_cursor.insertBlock()

            # 啟動定時器，每 10ms 更新輸出
            self.timer = QTimer(self.main_window)
            self.timer.setInterval(10)
            self.timer.timeout.connect(self.pull_text)
            self.timer.start()

        except Exception as error:
            # 發生錯誤時顯示錯誤訊息
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    def full_exit_program(self):
        """完全結束程式 / Fully exit program"""
        jeditor_logger.info("ExecManager full_exit_program")
        self.timer.stop()
        self.exit_program()
        self.main_window.exec_program = None

    def pull_text(self) -> None:
        jeditor_logger.info("ExecManager pull_text")
        # 從佇列中取出訊息並顯示到 QTextEdit
        # Pull text from queue and put in code result area
        try:
            # 處理標準輸出
            if not self.run_output_queue.empty():
                output_message = self.run_output_queue.get_nowait()
                output_message = str(output_message).strip()
                if output_message:
                    text_cursor = self.code_result.textCursor()
                    text_format = QTextCharFormat()
                    text_format.setForeground(actually_color_dict.get("normal_output_color"))
                    text_cursor.insertText(output_message, text_format)
                    text_cursor.insertBlock()
            # 處理錯誤輸出
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
            # 如果佇列是空的就忽略
            pass

        # 如果子程序已經結束(returncode 不為 None)，則完全退出
        if self.process.returncode == 0:
            self.full_exit_program()
        elif self.process.returncode is not None:
            self.full_exit_program()

        # 如果程式仍在執行，持續檢查狀態
        if self.still_run_program:
            # poll() 不會阻塞，只是更新 returncode
            self.process.poll()

    # 結束程式：將執行旗標設為 False，清理執行緒、佇列與子程序
    # Exit program: change run flag to false and clean read thread, queue, and process
    def exit_program(self) -> None:
        jeditor_logger.info("ExecManager exit_program")
        self.still_run_program = False
        # 清除讀取執行緒的引用
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        # 清空佇列
        self.print_and_clear_queue()
        # 如果子程序存在，則終止
        if self.process is not None:
            self.process.terminate()
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(f"Program exit with code {self.process.returncode}", text_format)
            text_cursor.insertBlock()
            self.process = None

    # 清空輸出與錯誤佇列
    # Pull all remaining strings in queues and reset them
    def print_and_clear_queue(self) -> None:
        jeditor_logger.info("ExecManager print_and_clear_queue")
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    # 從子程序 stdout 持續讀取資料並放入輸出佇列
    # Continuously read from process stdout and put into output queue
    def read_program_output_from_process(self) -> None:
        jeditor_logger.info("ExecManager read_program_output_from_process")
        while self.still_run_program:
            program_output_data: str = self.process.stdout.readline(
                self.program_buffer).decode(self.program_encoding, "replace")
            if self.process:
                self.process.stdout.flush()
            self.run_output_queue.put_nowait(program_output_data)

    # 從子程序 stderr 持續讀取資料並放入錯誤佇列
    # Continuously read from process stderr and put into error queue
    def read_program_error_output_from_process(self) -> None:
        jeditor_logger.info("ExecManager read_program_error_output_from_process")
        while self.still_run_program:
            program_error_output_data: str = self.process.stderr.readline(
                self.program_buffer).decode(self.program_encoding, "replace")
            if self.process:
                self.process.stderr.flush()
            self.run_error_queue.put_nowait(program_error_output_data)
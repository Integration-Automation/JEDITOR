from __future__ import annotations

import queue
import subprocess
import sys
from pathlib import Path
from threading import Thread
from typing import Union

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


class ExecManager(object):

    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,
            program_language: str = "python",
            program_encoding: str = "utf-8",
            program_buffer: int = 1024,
    ):
        """
        :param main_window: Pyside main window
        :param program_language: which program language
        :param program_encoding: which encoding
        """
        jeditor_logger.info(f"Init ExecManager "
                            f"main_window: {main_window} "
                            f"program_language: {program_language} "
                            f"program_encoding: {program_encoding} "
                            f"program_buffer: {program_buffer}")
        self.read_program_error_output_from_thread = None
        self.read_program_output_from_thread = None
        self.main_window: EditorWidget = main_window
        self.compiler_path = None
        self.code_result: Union[QTextEdit, None] = None
        self.code_result_cursor: Union[QTextEdit.textCursor, None] = None
        self.timer: Union[QTimer, None] = None
        self.still_run_program = True
        self.process: Union[subprocess.Popen, None] = None
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()
        self.program_language = program_language
        self.program_encoding = program_encoding
        self.program_buffer = program_buffer
        self.renew_path()
        run_instance_manager.instance_list.append(self)

    def renew_path(self) -> None:
        jeditor_logger.info("ExecManager renew_path")
        if self.main_window.python_compiler is None:
            # Renew compiler path
            if sys.platform in ["win32", "cygwin", "msys"]:
                venv_path = Path(str(Path.cwd()) + "/venv/Scripts")
            else:
                venv_path = Path(str(Path.cwd()) + "/venv/bin")
            self.compiler_path = check_and_choose_venv(venv_path)
        else:
            self.compiler_path = self.main_window.python_compiler

    def later_init(self) -> None:
        jeditor_logger.info("ExecManager later_init")
        # Enable timer and code result area
        if self.main_window is not None:
            self.code_result: QTextEdit = self.main_window.code_result
            self.timer = QTimer(self.main_window)
        else:
            raise JEditorException(je_editor_init_error)

    def exec_code(self, exec_file_name, exec_prefix: Union[str, list] = None) -> None:
        """
        :param exec_file_name: string file will open to run
        :param exec_prefix: user define exec prefix
        :return: if error return result and True else return result and False
        """
        jeditor_logger.info(f"ExecManager exec_code "
                            f"exec_file_name: {exec_file_name} "
                            f"exec_prefix: {exec_prefix}")
        try:
            self.exit_program()
            self.code_result.setPlainText("")
            file_path = Path(exec_file_name)
            reformat_os_file_path = str(file_path.absolute())
            # detect file is exist
            exec_file = reformat_os_file_path
            # run program
            if exec_prefix is None:
                execute_program_param = [self.compiler_path, exec_file]
            else:
                if isinstance(exec_prefix, str):
                    execute_program_param = [self.compiler_path, exec_prefix, exec_file]
                else:
                    execute_program_param = list()
                    execute_program_param.append(self.compiler_path)
                    for prefix in exec_prefix:
                        execute_program_param.append(prefix)
                    execute_program_param.append(exec_file)
            if sys.platform not in ["win32", "cygwin", "msys"]:
                execute_program_param = " ".join(execute_program_param)
            self.process = subprocess.Popen(
                execute_program_param,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            self.still_run_program = True
            # program output message queue thread
            self.read_program_output_from_thread = Thread(
                target=self.read_program_output_from_process,
                daemon=True
            )
            self.read_program_output_from_thread.start()
            # program error message queue thread
            self.read_program_error_output_from_thread = Thread(
                target=self.read_program_error_output_from_process,
                daemon=True
            )
            self.read_program_error_output_from_thread.start()
            # show which file execute
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(self.compiler_path + " " + reformat_os_file_path, text_format)
            text_cursor.insertBlock()
            # start tkinter_ui update
            # start timer
            self.timer = QTimer(self.main_window)
            self.timer.setInterval(10)
            self.timer.timeout.connect(self.pull_text)
            self.timer.start()
        except Exception as error:
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    def full_exit_program(self):
        jeditor_logger.info("ExecManager full_exit_program")
        self.timer.stop()
        self.exit_program()
        self.main_window.exec_program = None

    def pull_text(self) -> None:
        jeditor_logger.info("ExecManager pull_text")
        # Pull text from queue and put in code result area
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
        if self.process.returncode == 0:
            self.full_exit_program()
        elif self.process.returncode is not None:
            self.full_exit_program()
        if self.still_run_program:
            # poll return code
            self.process.poll()

    # Exit program change run flag to false and clean read thread and queue and process
    def exit_program(self) -> None:
        jeditor_logger.info("ExecManager exit_program")
        self.still_run_program = False
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        self.print_and_clear_queue()
        if self.process is not None:
            self.process.terminate()
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(f"Program exit with code {self.process.returncode}", text_format)
            text_cursor.insertBlock()
            self.process = None

    # Pull all remain string on queue and add to code result area
    def print_and_clear_queue(self) -> None:
        jeditor_logger.info("ExecManager print_and_clear_queue")
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def read_program_output_from_process(self) -> None:
        jeditor_logger.info("ExecManager read_program_output_from_process")
        while self.still_run_program:
            program_output_data: str = self.process.stdout.readline(
                self.program_buffer).decode(self.program_encoding, "replace")
            if self.process:
                self.process.stdout.flush()
            self.run_output_queue.put_nowait(program_output_data)

    def read_program_error_output_from_process(self) -> None:
        jeditor_logger.info("ExecManager read_program_error_output_from_process")
        while self.still_run_program:
            program_error_output_data: str = self.process.stderr.readline(
                self.program_buffer).decode(self.program_encoding, "replace")
            if self.process:
                self.process.stderr.flush()
            self.run_error_queue.put_nowait(program_error_output_data)

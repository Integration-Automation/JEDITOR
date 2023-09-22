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
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.exception.exception_tags import je_editor_init_error
from je_editor.utils.exception.exceptions import JEditorException
from je_editor.utils.venv_check.check_venv import check_and_choose_venv


class ShellManager(object):

    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,
            shell_encoding: str = "utf-8",
            program_buffer: int = 8192000,
            after_done_function: Union[None, Callable] = None
    ):
        """
        :param main_window: Pyside main window
        :param shell_encoding: shell command read output encoding
        :param program_buffer: buffer size
        """
        self.read_program_error_output_from_thread = None
        self.read_program_output_from_thread = None
        self.main_window: EditorWidget = main_window
        self.compiler_path = None
        self.code_result: [QTextEdit, None] = None
        self.timer: [QTimer, None] = None
        self.still_run_shell: bool = True
        self.process = None
        self.run_output_queue: queue = queue.Queue()
        self.run_error_queue: queue = queue.Queue()
        self.program_encoding: str = shell_encoding
        self.program_buffer: int = program_buffer
        self.after_done_function = after_done_function
        self.renew_path()
        run_instance_manager.instance_list.append(self)

    def renew_path(self) -> None:
        if self.main_window.python_compiler is None:
            # Renew compiler path
            if sys.platform in ["win32", "cygwin", "msys"]:
                venv_path = Path(os.getcwd() + "/venv/Scripts")
            else:
                venv_path = Path(os.getcwd() + "/venv/bin")
            self.compiler_path = check_and_choose_venv(venv_path)
        else:
            self.compiler_path = self.main_window.python_compiler

    def later_init(self) -> None:
        if self.main_window is not None:
            self.code_result: QTextEdit = self.main_window.code_result
        else:
            raise JEditorException(je_editor_init_error)

    def exec_shell(self, shell_command: [str, list]) -> None:
        """
        :param shell_command: shell command will run
        :return: if error return result and True else return result and False
        """
        try:
            self.exit_program()
            self.code_result.setTextColor(actually_color_dict.get("normal_output_color"))
            self.code_result.setPlainText("")
            if sys.platform in ["win32", "cygwin", "msys"]:
                args = shell_command
            else:
                args = shlex.split(shell_command)
            self.code_result.append(str(args))
            self.process = subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=True,
            )
            self.still_run_shell = True
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
            # start timer
            self.timer = QTimer(self.main_window)
            self.timer.setInterval(1)
            self.timer.timeout.connect(self.pull_text)
            self.timer.start()
        except Exception as error:
            self.code_result.setTextColor(actually_color_dict.get("error_output_color"))
            self.code_result.append(str(error))
            self.code_result.setTextColor(actually_color_dict.get("normal_output_color"))
            if self.process is not None:
                self.process.terminate()

    # tkinter_ui update method
    def pull_text(self) -> None:
        try:
            self.code_result.setTextColor(actually_color_dict.get("normal_output_color"))
            if not self.run_output_queue.empty():
                output_message = self.run_output_queue.get_nowait()
                output_message = str(output_message).strip()
                if output_message:
                    self.code_result.append(output_message)
            self.code_result.setTextColor(actually_color_dict.get("error_output_color"))
            if not self.run_error_queue.empty():
                error_message = self.run_error_queue.get_nowait()
                error_message = str(error_message).strip()
                if error_message:
                    self.code_result.append(error_message)
            self.code_result.setTextColor(actually_color_dict.get("normal_output_color"))
        except queue.Empty:
            pass
        if self.process.returncode == 0:
            self.process_run_over()
        elif self.process.returncode is not None:
            self.process_run_over()
        if self.still_run_shell:
            # poll return code
            self.process.poll()

    def process_run_over(self):
        self.timer.stop()
        self.exit_program()
        self.main_window.exec_shell = None
        if self.after_done_function is not None:
            self.after_done_function()

    # exit program change run flag to false and clean read thread and queue and process
    def exit_program(self) -> None:
        self.still_run_shell = False
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        self.print_and_clear_queue()
        if self.process is not None:
            self.process.terminate()
            self.code_result.append(f"Shell command exit with code {self.process.returncode}")
            self.process = None

    def print_and_clear_queue(self) -> None:
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def read_program_output_from_process(self) -> None:
        while self.still_run_shell:
            program_output_data = self.process.stdout.raw.read(
                self.program_buffer) \
                .decode(self.program_encoding)
            self.run_output_queue.put_nowait(program_output_data)

    def read_program_error_output_from_process(self) -> None:
        while self.still_run_shell:
            program_error_output_data = self.process.stderr.raw.read(
                self.program_buffer) \
                .decode(self.program_encoding)
            self.run_error_queue.put_nowait(program_error_output_data)

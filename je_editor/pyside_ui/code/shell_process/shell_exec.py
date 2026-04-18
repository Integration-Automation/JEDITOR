from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Union, Callable

from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.code.base_process_manager import BaseProcessManager
from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.exception.exception_tags import je_editor_init_error
from je_editor.utils.exception.exceptions import JEditorException
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.venv_check.check_venv import check_and_choose_venv


class ShellManager(BaseProcessManager):
    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,
            shell_encoding: str = "utf-8",
            program_buffer: int = 1024,
            after_done_function: Union[None, Callable] = None
    ) -> None:
        jeditor_logger.info(f"Init ShellManager "
                            f"main_window: {main_window} "
                            f"shell_encoding: {shell_encoding} "
                            f"program_buffer: {program_buffer} "
                            f"after_done_function: {after_done_function}")
        super().__init__(
            main_window=main_window,
            encoding=shell_encoding,
            buffer_size=program_buffer,
        )
        self.compiler_path = None
        self.after_done_function = after_done_function
        self.renew_path()

    @property
    def still_run_shell(self) -> bool:
        return self.still_running

    @still_run_shell.setter
    def still_run_shell(self, value: bool) -> None:
        self.still_running = value

    def renew_path(self) -> None:
        """更新 Python 編譯器路徑 / Renew Python compiler path"""
        jeditor_logger.info("ShellManager renew_path")
        if self.main_window is None or self.main_window.python_compiler is None:
            if sys.platform in ["win32", "cygwin", "msys"]:
                venv_path = Path(os.getcwd()) / "venv" / "Scripts"
            else:
                venv_path = Path(os.getcwd()) / "venv" / "bin"
            self.compiler_path = check_and_choose_venv(venv_path)
        else:
            self.compiler_path = self.main_window.python_compiler

    def later_init(self) -> None:
        """延遲初始化，綁定輸出視窗 / Late initialization, bind output QTextEdit"""
        jeditor_logger.info("ShellManager later_init")
        if self.main_window is not None:
            self.code_result: QTextEdit = self.main_window.code_result
        else:
            raise JEditorException(je_editor_init_error)

    def exec_shell(self, shell_command: Union[str, list]) -> None:
        """
        執行 shell 指令
        Execute shell command
        """
        jeditor_logger.info(f"ShellManager exec_shell, shell_command: {shell_command}")
        try:
            self.exit_program()
            self.code_result.setPlainText("")
            if sys.platform in ["win32", "cygwin", "msys"]:
                args = shell_command
            else:
                args = shell_command if isinstance(shell_command, str) else " ".join(shell_command)
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(str(args), text_format)
            text_cursor.insertBlock()
            # shell=True is required: this is the user-facing shell execution feature
            # of the editor, invoked only with commands the user explicitly types.
            # Not a user-input-driven pipeline from untrusted data.
            self.process = subprocess.Popen(  # noqa: S602  # nosec B602
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=True,
            )
            self.still_run_shell = True

            self._start_reader_threads()
            self._start_pull_timer()

        except Exception as error:
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("error_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    def process_run_over(self) -> None:
        """當子程序結束時呼叫 / Called when subprocess finishes"""
        jeditor_logger.info("ShellManager process_run_over")
        if self.timer is not None:
            self.timer.stop()
        self.exit_program()
        self.main_window.exec_shell = None
        run_instance_manager.remove_instance(self)
        if self.after_done_function is not None:
            self.after_done_function()

    def _on_process_finished(self) -> None:
        """子程序結束時呼叫 / Called when process finishes"""
        self.process_run_over()

    def _exit_message_prefix(self) -> str:
        return "Shell command"

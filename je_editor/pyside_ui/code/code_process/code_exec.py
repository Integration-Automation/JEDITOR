from __future__ import annotations

import subprocess  # nosec B404 - 以引數清單呼叫編譯器/直譯器，shell=False
import sys
from pathlib import Path
from typing import Union

from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import QTextEdit

from je_editor.pyside_ui.code.base_process_manager import BaseProcessManager
from je_editor.pyside_ui.code.running_process_manager import run_instance_manager
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict
from je_editor.utils.exception.exception_tags import je_editor_init_error
from je_editor.utils.exception.exceptions import JEditorException
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.venv_check.check_venv import check_and_choose_venv, get_venv_path


class ExecManager(BaseProcessManager):
    """
    程式執行管理器
    Execution manager for running code inside the editor.
    """

    def __init__(
            self,
            main_window: Union[EditorWidget, None] = None,
            program_language: str = "python",
            program_encoding: str = "utf-8",
            program_buffer: int = 1024,
    ) -> None:
        jeditor_logger.info(f"Init ExecManager "
                            f"main_window: {main_window} "
                            f"program_language: {program_language} "
                            f"program_encoding: {program_encoding} "
                            f"program_buffer: {program_buffer}")
        super().__init__(
            main_window=main_window,
            encoding=program_encoding,
            buffer_size=program_buffer,
        )
        self.compiler_path = None
        self.code_result_cursor: Union[QTextEdit.textCursor, None] = None
        self.program_language = program_language
        self.renew_path()

    @property
    def still_run_program(self) -> bool:
        return self.still_running

    @still_run_program.setter
    def still_run_program(self, value: bool) -> None:
        self.still_running = value

    def renew_path(self) -> None:
        """更新 Python 直譯器路徑 / Renew compiler path"""
        jeditor_logger.info("ExecManager renew_path")
        if self.main_window is None or self.main_window.python_compiler is None:
            self.compiler_path = check_and_choose_venv(get_venv_path())
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

    def exec_code(self, exec_file_name: str, exec_prefix: Union[str, list] = None) -> None:
        """
        執行指定檔案
        Execute given file
        """
        jeditor_logger.info(f"ExecManager exec_code "
                            f"exec_file_name: {exec_file_name} "
                            f"exec_prefix: {exec_prefix}")
        try:
            self.exit_program()
            self.code_result.setPlainText("")
            file_path = Path(exec_file_name)
            reformat_os_file_path = str(file_path.absolute())
            exec_file = reformat_os_file_path

            if exec_prefix is None:
                execute_program_param = [self.compiler_path, exec_file]
            else:
                if isinstance(exec_prefix, str):
                    execute_program_param = [self.compiler_path, exec_prefix, exec_file]
                else:
                    execute_program_param = [self.compiler_path] + exec_prefix + [exec_file]

            # 以引數清單呼叫使用者選定的編譯器/直譯器，shell=False
            # Invoke user-selected compiler/interpreter via argv list; no shell
            # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            self.process = subprocess.Popen(  # noqa: S603  # nosec B603
                execute_program_param,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            self.still_run_program = True

            self._start_reader_threads()

            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(self.compiler_path + " " + reformat_os_file_path, text_format)
            text_cursor.insertBlock()

            self._start_pull_timer()

        except Exception as error:
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("error_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    def exec_with_plugin_config(self, exec_file_name: str, run_config: dict) -> None:
        """
        使用插件的 PLUGIN_RUN_CONFIG 執行程式。
        Execute a program using plugin's PLUGIN_RUN_CONFIG.
        """
        jeditor_logger.info(f"ExecManager exec_with_plugin_config "
                            f"exec_file_name: {exec_file_name} "
                            f"run_config: {run_config}")
        try:
            self.exit_program()
            self.code_result.setPlainText("")
            file_path = Path(exec_file_name)
            reformat_os_file_path = str(file_path.absolute())

            compiler = run_config.get("compiler", "")
            args = list(run_config.get("args", ()))
            compile_then_run = run_config.get("compile_then_run", False)
            output_flag = run_config.get("output_flag", "")

            if compile_then_run:
                output_path = str(file_path.with_suffix(".exe" if sys.platform == "win32" else ""))

                compile_cmd = [compiler] + args + [reformat_os_file_path]
                if output_flag:
                    compile_cmd += [output_flag, output_path]

                text_cursor = self.code_result.textCursor()
                text_format = QTextCharFormat()
                text_format.setForeground(actually_color_dict.get("normal_output_color"))
                text_cursor.insertText("[Compile] " + " ".join(compile_cmd), text_format)
                text_cursor.insertBlock()

                # 以引數清單呼叫外部編譯器，shell=False
                # Invoke external compiler via argv list; no shell
                # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
                compile_process = subprocess.Popen(  # noqa: S603  # nosec B603
                    compile_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                )
                stdout, stderr = compile_process.communicate(timeout=60)

                if stderr:
                    text_format_err = QTextCharFormat()
                    text_format_err.setForeground(actually_color_dict.get("error_output_color"))
                    text_cursor.insertText(stderr.decode(self.program_encoding, "replace"), text_format_err)
                    text_cursor.insertBlock()

                if compile_process.returncode != 0:
                    text_cursor.insertText(
                        f"Compilation failed with code {compile_process.returncode}", text_format
                    )
                    text_cursor.insertBlock()
                    return

                if stdout:
                    text_cursor.insertText(stdout.decode(self.program_encoding, "replace"), text_format)
                    text_cursor.insertBlock()

                execute_program_param = [output_path]
                display_cmd = output_path
            else:
                execute_program_param = [compiler] + args + [reformat_os_file_path]
                display_cmd = " ".join(execute_program_param)

            # 以引數清單呼叫使用者選定的編譯器/直譯器，shell=False
            # Invoke user-selected compiler/interpreter via argv list; no shell
            # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
            self.process = subprocess.Popen(  # noqa: S603  # nosec B603
                execute_program_param,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False,
            )
            self.still_run_program = True

            self._start_reader_threads()

            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText("[Run] " + display_cmd, text_format)
            text_cursor.insertBlock()

            self._start_pull_timer()

        except Exception as error:
            text_cursor = self.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("error_output_color"))
            text_cursor.insertText(str(error), text_format)
            text_cursor.insertBlock()
            if self.process is not None:
                self.process.terminate()

    def full_exit_program(self) -> None:
        """完全結束程式 / Fully exit program"""
        jeditor_logger.info("ExecManager full_exit_program")
        if self.timer is not None:
            self.timer.stop()
        self.exit_program()
        self.main_window.exec_program = None
        run_instance_manager.remove_instance(self)

    def _on_process_finished(self) -> None:
        """子程序結束時呼叫 / Called when process finishes"""
        self.full_exit_program()

    def _exit_message_prefix(self) -> str:
        return "Program"

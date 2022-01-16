import sys
import os.path
import queue
import shutil
import subprocess
from pathlib import Path
from threading import Thread
from tkinter import DISABLED
from tkinter import END
from tkinter import NORMAL

from je_editor.utils.exception.je_editor_exception_tag import file_not_fond_error
from je_editor.utils.exception.je_editor_exception_tag import python_not_found_error
from je_editor.utils.exception.je_editor_exceptions import JEditorExecException

from je_editor.utils.text_process.language_data_module.language_compiler_data_module import language_compiler
from je_editor.utils.text_process.language_data_module.language_param_data_module import language_compiler_param


class ExecManager(object):

    def __init__(
            self,
            run_result,
            process_error_function,
            main_window,
            running_menu,
            program_language="python",
            program_encoding="utf-8"
    ):
        self.read_program_error_output_from_thread = None
        self.read_program_output_from_thread = None
        self.main_window = main_window
        self.still_run_program = True
        self.run_result = run_result
        self.process_error_function = process_error_function
        self.process = None
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()
        self.program_language = program_language
        self.running_menu = running_menu
        self.program_encoding = program_encoding

    def exec_code(self, exec_file_name):
        """
        :param exec_file_name: string file will open to run
        :return: if error return result and True else return result and False
        """
        self.exit_program()
        self.running_menu.entryconfigure(1, label="Rerun")
        self.running_menu.entryconfigure(3, state="normal")
        self.run_result.configure(state=NORMAL)
        self.run_result.delete("1.0", "end-1c")
        self.run_result.configure(state=DISABLED)
        reformat_os_file_path = os.path.abspath(exec_file_name)
        try:
            if not Path(exec_file_name).exists():
                raise JEditorExecException(file_not_fond_error)
        except OSError as error:
            raise JEditorExecException(error)
        if sys.platform in ["linux", "linux2", "win32", "cygwin", "msys"]:
            compiler_path = shutil.which(self.program_language)
        else:
            compiler_path = shutil.which(self.program_language)
        if compiler_path is None:
            raise JEditorExecException(python_not_found_error)
        exec_command = reformat_os_file_path

        if self.program_language in language_compiler:
            self.process = subprocess.Popen(
                [
                    shutil.which(language_compiler.get(self.program_language)),
                    language_compiler_param.get(self.program_language),
                    reformat_os_file_path
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            while self.process.returncode is None:
                self.process.poll()
        self.process = subprocess.Popen([compiler_path, exec_command],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=False)
        self.still_run_program = True
        self.read_program_output_from_thread = Thread(
            target=self.read_program_output_from_process,
        )
        self.read_program_output_from_thread.setDaemon(True)
        self.read_program_output_from_thread.start()
        self.read_program_error_output_from_thread = Thread(
            target=self.read_program_error_output_from_process,
        )
        self.read_program_error_output_from_thread.setDaemon(True)
        self.read_program_error_output_from_thread.start()
        self.run_result.configure(state=NORMAL)
        self.run_result.insert(END, compiler_path + " " + reformat_os_file_path + "\n")
        self.run_result.configure(state=DISABLED)
        self.edit_tkinter_text()

    def edit_tkinter_text(self):
        self.run_result.configure(state=NORMAL)
        if not self.run_error_queue.empty():
            error_message = self.run_error_queue.get_nowait()
            self.process_error_function(self.run_result, error_message)
        if not self.run_output_queue.empty():
            output_message = self.run_output_queue.get_nowait()
            self.run_result.insert(END, output_message)
        self.run_result.configure(state=DISABLED)
        if self.process.returncode is not None:
            self.exit_program()
        if self.still_run_program:
            self.main_window.after(1, self.edit_tkinter_text)
            self.process.poll()
        else:
            self.running_menu.entryconfigure(1, label="Run")
            self.running_menu.entryconfigure(3, state="disable")

    def exit_program(self):
        self.still_run_program = False
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()
        if self.process is not None:
            self.process.terminate()

    def read_program_output_from_process(self):
        while self.still_run_program:
            program_output_data = self.process.stdout.raw.read(1024).decode(self.program_encoding)
            self.run_output_queue.put(program_output_data)

    def read_program_error_output_from_process(self):
        while self.still_run_program:
            program_error_output_data = self.process.stderr.raw.read(1024).decode(self.program_encoding)
            self.run_error_queue.put(program_error_output_data)

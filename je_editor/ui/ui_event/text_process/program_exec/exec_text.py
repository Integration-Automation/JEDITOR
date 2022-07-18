import os.path
import queue
import shutil
import subprocess
from pathlib import Path
from threading import Thread
from tkinter import DISABLED
from tkinter import END
from tkinter import NORMAL

from je_editor.utils.exception.exception_tags import file_not_fond_error
from je_editor.utils.exception.exception_tags import compiler_not_found_error
from je_editor.utils.exception.exceptions import JEditorExecException

from je_editor.ui.ui_utils.language_data_module.language_compiler_data_module import language_compiler
from je_editor.ui.ui_utils.language_data_module.language_param_data_module import language_compiler_param


class ExecManager(object):

    def __init__(
            self,
            program_run_result_textarea,
            process_error_function,
            main_window,
            running_menu,
            program_language="python3",
            program_encoding="utf-8"
    ):
        """
        :param program_run_result_textarea:  program run result textarea
        :param process_error_function: when process error call this function
        :param main_window: tkinter main window
        :param running_menu: menu when running change state
        :param program_language: which program language
        :param program_encoding: which encoding
        """
        self.read_program_error_output_from_thread = None
        self.read_program_output_from_thread = None
        self.main_window = main_window
        self.still_run_program = True
        self.run_program_result_textarea = program_run_result_textarea
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
        try:
            self.exit_program()
            self.running_menu.entryconfigure(1, label="Rerun")
            self.running_menu.entryconfigure(3, state="normal")
            self.run_program_result_textarea.configure(state=NORMAL)
            self.run_program_result_textarea.delete("1.0", "end-1c")
            self.run_program_result_textarea.configure(state=DISABLED)
            reformat_os_file_path = os.path.abspath(exec_file_name)
            # detect file is exist
            try:
                if not Path(exec_file_name).exists():
                    raise JEditorExecException(file_not_fond_error)
            except OSError as error:
                raise JEditorExecException(error)
            compiler_path = shutil.which(self.program_language)
            if compiler_path is None and self.program_language == "python3":
                compiler_path = shutil.which("python")
            if compiler_path is None:
                raise JEditorExecException(compiler_not_found_error)
            exec_file = reformat_os_file_path
            # precompile
            if self.program_language in language_compiler:
                self.process = subprocess.Popen(
                    [
                        shutil.which(language_compiler.get(self.program_language)),
                        language_compiler_param.get(self.program_language),
                        reformat_os_file_path
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                while self.process.returncode is None:
                    self.process.poll()
            # run program
            execute_program_list = [compiler_path, exec_file]
            self.process = subprocess.Popen(
                execute_program_list,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False
            )
            self.still_run_program = True
            # program output message queue thread
            self.read_program_output_from_thread = Thread(
                target=self.read_program_output_from_process,
                daemon=True
            ).start()
            # program error message queue thread
            self.read_program_error_output_from_thread = Thread(
                target=self.read_program_error_output_from_process,
                daemon=True
            ).start()
            # show which file execute
            self.run_program_result_textarea.configure(state=NORMAL)
            self.run_program_result_textarea.insert(END, compiler_path + " " + reformat_os_file_path + "\n")
            self.run_program_result_textarea.configure(state=DISABLED)
            # start ui update
            self.edit_tkinter_text()
        except Exception as error:
            print(repr(error))

    # ui update method
    def edit_tkinter_text(self):
        self.run_program_result_textarea.configure(state=NORMAL)
        if not self.run_error_queue.empty():
            error_message = self.run_error_queue.get_nowait()
            self.process_error_function(self.run_program_result_textarea, error_message)
        if not self.run_output_queue.empty():
            output_message = self.run_output_queue.get_nowait()
            self.run_program_result_textarea.insert(END, output_message)
        self.run_program_result_textarea.configure(state=DISABLED)
        if self.process.returncode is not None:
            self.exit_program()
        if self.still_run_program:
            self.main_window.after(1, self.edit_tkinter_text)
            # poll return code
            self.process.poll()
        else:
            self.running_menu.entryconfigure(1, label="Run")
            self.running_menu.entryconfigure(3, state="disable")

    # exit program change run flag to false and clean read thread and queue and process
    def exit_program(self):
        self.still_run_program = False
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        self.print_and_clear_queue()
        if self.process is not None:
            self.process.terminate()

    def print_and_clear_queue(self):
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def read_program_output_from_process(self):
        while self.still_run_program:
            program_output_data = self.process.stdout.raw.read(1024000).decode(self.program_encoding)
            self.run_output_queue.put_nowait(program_output_data)

    def read_program_error_output_from_process(self):
        while self.still_run_program:
            program_error_output_data = self.process.stderr.raw.read(1024000).decode(self.program_encoding)
            self.run_error_queue.put_nowait(program_error_output_data)

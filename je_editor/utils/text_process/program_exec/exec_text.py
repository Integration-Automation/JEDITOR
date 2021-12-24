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


class ExecManager(object):

    def __init__(self, run_result, process_error_function, main_window):
        self.main_window = main_window
        self.still_run_program = True
        self.run_result = run_result
        self.process_error_function = process_error_function
        self.process = None
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def exec_code(self, exec_file_name):
        """
        :param exec_file_name: string file will open to run
        :return: if error return result and True else return result and False
        """
        reformat_os_file_path = os.path.abspath(exec_file_name)
        try:
            if not Path(exec_file_name).exists():
                raise JEditorExecException(file_not_fond_error)
        except OSError as error:
            raise JEditorExecException(error)
        python_path = shutil.which("python")
        if python_path is None:
            raise JEditorExecException(python_not_found_error)
        exec_command = reformat_os_file_path
        self.process = subprocess.Popen([python_path + " ", exec_command],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        shell=False)
        read_program_output_from_thread = Thread(target=self.read_program_output_from_process)
        read_program_output_from_thread.setDaemon(True)
        read_program_output_from_thread.start()
        read_program_error_output_from_thread = Thread(target=self.read_program_error_output_from_process)
        read_program_error_output_from_thread.setDaemon(True)
        read_program_error_output_from_thread.start()
        print("execute: " + reformat_os_file_path)
        self.edit_tkinter_text()

    def edit_tkinter_text(self):
        self.run_result.configure(state=NORMAL)
        if not self.run_error_queue.empty():
            self.run_result.insert(END, self.run_error_queue.get())
        if not self.run_output_queue.empty():
            self.run_result.insert(END, self.run_output_queue.get())
        self.run_result.configure(state=DISABLED)
        if self.still_run_program:
            self.main_window.after(10, self.edit_tkinter_text)

    def exit_program(self):
        self.still_run_program = False

    def read_program_output_from_process(self):
        while self.still_run_program:
            program_output_data = self.process.stdout.raw.read(1024).decode()
            self.run_output_queue.put(program_output_data)

    def read_program_error_output_from_process(self):
        while self.still_run_program:
            program_error_output_data = self.process.stderr.raw.read(1024).decode()
            self.run_error_queue.put(program_error_output_data)

import queue
import subprocess
import tkinter
import typing
from threading import Thread
from tkinter import DISABLED
from tkinter import END
from tkinter import NORMAL


class ShellManager(object):

    def __init__(
            self,
            main_window: tkinter.Tk,
            run_shell_result_textarea: tkinter.Text,
            process_error_function: typing.Callable,
            shell_encoding: str = "utf-8",
            program_buffer: int = 10240000,
    ):
        """
        :param run_shell_result_textarea:  program run result textarea
        :param process_error_function: when process error call this function
        :param main_window: tkinter main window
        """
        self.read_program_error_output_from_thread = None
        self.read_program_output_from_thread = None
        self.main_window = main_window
        self.run_shell_result_textarea = run_shell_result_textarea
        self.process_error_function = process_error_function
        self.still_run_shell = True
        self.process = None
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()
        self.program_encoding = shell_encoding
        self.program_buffer = program_buffer

    def exec_shell(self, shell_command: str):
        """
        :param shell_command: shell command will run
        :return: if error return result and True else return result and False
        """
        try:
            self.exit_program()
            self.run_shell_result_textarea.configure(state=NORMAL)
            self.run_shell_result_textarea.delete("1.0", "end-1c")
            self.run_shell_result_textarea.configure(state=DISABLED)
            # run shell command
            args = shell_command.split()
            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
            self.still_run_shell = True
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
            # start ui update
            self.edit_tkinter_text()
        except Exception as error:
            self.run_shell_result_textarea.configure(state=NORMAL)
            self.run_shell_result_textarea.insert(END, str(error), "warning", "\n")
            self.run_shell_result_textarea.configure(state=DISABLED)

    # ui update method
    def edit_tkinter_text(self):
        try:
            self.run_shell_result_textarea.configure(state=NORMAL)
            if not self.run_error_queue.empty():
                error_message = self.run_error_queue.get_nowait()
                self.process_error_function(self.run_shell_result_textarea, error_message)
            if not self.run_output_queue.empty():
                output_message = self.run_output_queue.get_nowait()
                self.run_shell_result_textarea.insert(END, output_message)
            self.run_shell_result_textarea.configure(state=DISABLED)
        except queue.Empty:
            pass
        if self.process.returncode == 0:
            self.exit_program()
        elif self.process.returncode is not None:
            self.exit_program()
        if self.still_run_shell:
            self.main_window.after(1, self.edit_tkinter_text)
            # poll return code
            self.process.poll()

    # exit program change run flag to false and clean read thread and queue and process
    def exit_program(self):
        self.still_run_shell = False
        if self.read_program_output_from_thread is not None:
            self.read_program_output_from_thread = None
        if self.read_program_error_output_from_thread is not None:
            self.read_program_error_output_from_thread = None
        self.print_and_clear_queue()
        if self.process is not None:
            self.process.terminate()

    def print_and_clear_queue(self):
        try:
            self.run_shell_result_textarea.configure(state=NORMAL)
            for std_output in iter(self.run_output_queue.get_nowait, None):
                self.run_shell_result_textarea.insert(END, std_output)
            for std_err in iter(self.run_error_queue.get_nowait, None):
                self.run_shell_result_textarea.insert(END, std_err, "warning", "\n")
            self.run_shell_result_textarea.configure(state=DISABLED)
        except queue.Empty:
            pass
        self.run_output_queue = queue.Queue()
        self.run_error_queue = queue.Queue()

    def read_program_output_from_process(self):
        while self.still_run_shell:
            program_output_data = self.process.stdout.raw.read(self.program_buffer) \
                .decode(self.program_encoding)
            self.run_output_queue.put_nowait(program_output_data)

    def read_program_error_output_from_process(self):
        while self.still_run_shell:
            program_error_output_data = self.process.stderr.raw.read(self.program_buffer) \
                .decode(self.program_encoding)
            self.run_error_queue.put_nowait(program_error_output_data)

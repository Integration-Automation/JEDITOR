import tkinter
from tkinter import *
from tkinter import ttk

from je_editor.utils.code_tag.tag_keyword import HighlightText
from je_editor.utils.editor_content.content_save import open_content_and_start
from je_editor.utils.editor_content.content_save import save_content_and_quit
from je_editor.utils.file.open_file import open_file
from je_editor.utils.file.open_file import read_file
from je_editor.utils.file.save_file import SaveThread
from je_editor.utils.file.save_file import save_file
from je_editor.utils.text_process.exec_text import exec_code
from je_editor.utils.text_process.shell_text import run_on_shell


def start_editor(use_theme=None):
    EditorMain(use_theme=use_theme).start_editor()


class EditorMain(object):

    def start_editor(self):
        if self.auto_save is not None:
            self.auto_save.start()
        self.main_window.mainloop()

    def close_event(self):
        if self.file_to_output_content is not None:
            save_content_and_quit(self.file_to_output_content)
        self.main_window.destroy()

    def open_file_to_read(self, event=None):
        temp_to_check_file = open_file()
        if temp_to_check_file is not None:
            self.file_to_output_content = temp_to_check_file[0]
            self.code_editor.delete(self.start_position, self.end_position)
            self.code_editor.insert(self.end_position, temp_to_check_file[1])
            self.current_file = temp_to_check_file[0]
            if self.current_file is not None and self.auto_save is None:
                self.auto_save = SaveThread(self.current_file, self.code_editor)
                self.auto_save.start()

    def save_file_to_open(self, event=None):
        temp_to_check_file = save_file(self.code_editor.get(self.start_position, self.end_position))
        if temp_to_check_file is not None:
            self.current_file = temp_to_check_file[0]
            if self.current_file is not None and self.auto_save is None:
                self.auto_save = SaveThread(self.current_file, self.code_editor)
                self.auto_save.start()

    def open_last_edit_file(self):
        temp_to_check_file = read_file(self.file_to_output_content)
        if temp_to_check_file is not None:
            self.code_editor.delete(self.start_position, self.end_position)
            self.code_editor.insert(self.end_position, temp_to_check_file[1])
            return temp_to_check_file[0]

    def exec_code(self, event=None):
        self.run_result.configure(state="normal")
        self.run_result.delete(self.start_position, self.end_position)
        self.run_result.insert(self.start_position,
                               exec_code(self.code_editor.get(self.start_position, self.end_position)))
        self.run_result.configure(state="disabled")

    def run_on_shell(self, event=None):
        self.run_result.configure(state="normal")
        self.run_result.delete(self.start_position, self.end_position)
        self.run_result.insert(self.start_position,
                               run_on_shell(self.code_editor.get(self.start_position, self.end_position)))
        self.run_result.configure(state="disabled")

    def show_popup_menu(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.popup_menu.grab_release()

    # default event
    def do_test(self, event=None):
        self.test_run = True
        print("test")

    def __init__(self, use_theme=None, main_window=Tk()):
        """
        :param main_window: Tk instance
        """
        # style
        self.style = ttk.Style()
        if use_theme is not None:
            self.style.theme_use(use_theme)
        # set main window title and add main frame
        self.main_window = main_window
        self.main_window.title("je_editor")
        self.code_edit_frame = ttk.Frame(self.main_window, padding="3 3 12 12")
        self.code_edit_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        self.run_result_frame = ttk.Frame(self.main_window, padding="3 3 12 12")
        self.run_result_frame.grid(column=0, row=1, sticky=(N, W, E, S))
        # Text start and end position
        self.start_position = "1.0"
        self.end_position = "end-1c"
        # set code edit
        self.code_editor = Text(self.code_edit_frame, undo=True, autoseparators=True, maxundo=-1)
        self.code_editor_scrollbar_y = ttk.Scrollbar(orient="vertical", command=self.code_editor.yview)
        self.code_editor["yscrollcommand"] = self.code_editor_scrollbar_y.set
        self.code_editor.grid(column=0, row=0, sticky=(N, W, E, S))
        self.code_editor_scrollbar_y.grid(column=1, row=0)
        self.code_editor.configure(state="normal")
        # run result
        self.run_result = Text(self.run_result_frame)
        self.run_result_scrollbar_y = ttk.Scrollbar(orient="vertical", command=self.run_result.yview)
        self.run_result["yscrollcommand"] = self.run_result_scrollbar_y.set
        self.run_result.grid(column=0, row=1, sticky=(N, W, E, S))
        self.run_result_scrollbar_y.grid(column=1, row=1)
        self.run_result.configure(state="disabled")
        self.run_result.bind("<1>", lambda event: self.run_result.focus_set())
        # Menubar
        # Main menu
        self.menu = tkinter.Menu(self.main_window)
        # File menu
        self.file_menu = tkinter.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Save File", command=self.save_file_to_open)
        self.file_menu.add_command(label="Open File", command=self.open_file_to_read)
        # Function menu
        self.function_menu = tkinter.Menu(self.menu, tearoff=0)
        self.function_menu.add_command(label="Run", command=self.exec_code)
        self.function_menu.add_command(label="Run on shell", command=self.run_on_shell)
        # Popup menu
        self.popup_menu = Menu(self.main_window, tearoff=0)
        self.popup_menu.add_command(label="Run", command=self.exec_code)
        self.popup_menu.add_command(label="Run on shell", command=self.run_on_shell)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Save File", command=self.save_file_to_open)
        self.popup_menu.add_command(label="Open File", command=self.open_file_to_read)
        self.main_window.bind("<Button-3>", self.show_popup_menu)
        # add and config
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.menu.add_cascade(label="Function", menu=self.function_menu)
        self.main_window.config(menu=self.menu)
        # set resize
        self.code_edit_frame.columnconfigure(0, weight=1)
        self.code_edit_frame.rowconfigure(0, weight=1)
        self.run_result_frame.columnconfigure(0, weight=1)
        self.run_result_frame.rowconfigure(1, weight=1)
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.rowconfigure(0, weight=1)
        # Highlight word
        HighlightText(self.code_editor)
        # current file
        self.current_file = None
        # file to output content
        self.file_to_output_content = open_content_and_start()
        if self.file_to_output_content is not None:
            self.current_file = self.open_last_edit_file()
        # close event
        self.main_window.protocol("WM_DELETE_WINDOW", self.close_event)
        # bind
        self.main_window.bind("<Control-Key-o>", self.open_file_to_read)
        self.main_window.bind("<Control-Key-s>", self.save_file_to_open)
        self.main_window.bind("<Control-Key-F5>", self.exec_code)
        self.main_window.bind("<Control-Key-F6>", self.run_on_shell)
        # is this test run?
        self.test_run = False
        # Auto save thread
        self.auto_save = None
        if self.current_file is not None:
            self.auto_save = SaveThread(self.current_file, self.code_editor)

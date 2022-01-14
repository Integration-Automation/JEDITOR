import tkinter
from tkinter import E
from tkinter import Menu
from tkinter import N
from tkinter import S
from tkinter import Text
from tkinter import Tk
from tkinter import W
from tkinter import ttk

from je_editor.ui.ui_event.auto_save.start_auto_save.start_auto_save import start_auto_save
from je_editor.ui.ui_event.close.close_event import close_event
from je_editor.ui.ui_event.execute.execute_code.exec_code import execute_code
from je_editor.ui.ui_event.execute.execute_shell_command.run_on_shell import execute_shell_command
from je_editor.ui.ui_event.open_file.open_file_to_read.open_file_to_read import open_file_to_read
from je_editor.ui.ui_event.open_file.open_last_edit_file.open_last_edit_file import open_last_edit_file
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_to_open
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_then_can_run
from je_editor.utils.code_tag.tag_keyword import HighlightText
from je_editor.utils.editor_content.content_save import open_content_and_start
from je_editor.utils.text_process.program_exec.exec_text import ExecManager
from je_editor.utils.text_process.program_exec.process_error import process_error_text
from je_editor.ui.ui_utils.font.font import get_font
from je_editor.ui.ui_event.change_font.change_font import change_font
from je_editor.ui.ui_event.change_font.change_font import change_font_size
from je_editor.ui.ui_event.execute.execute_code.exec_code import stop_program
from je_editor.utils.encoding.encoding_data_module import encoding_list
from je_editor.ui.ui_event.encoding.set_encoding import set_encoding
from je_editor.ui.ui_event.language.set_language import set_language
from je_editor.utils.language.language_data_module import language_list


def start_editor(use_theme=None):
    EditorMain(use_theme=use_theme).start_editor()


class EditorMain(object):

    # start editor and start auto save if auto save not start
    def start_editor(self):
        self.auto_save = start_auto_save(self.auto_save, self.current_file, self.code_editor)
        self.main_window.mainloop()

    # editor close event
    def close_event(self):
        close_event(self.current_file, self.main_window, self.exec_manager)

    # editor open file
    def open_file_to_read(self, event=None):
        temp = open_file_to_read(self.code_editor)
        self.file_from_output_content = temp
        self.current_file = temp
        self.highlight_text.search()
        self.auto_save = start_auto_save(self.auto_save, self.current_file, self.code_editor)

    # save editor file
    def save_file_to_open(self, event=None):
        self.current_file = save_file_to_open(self.code_editor)
        self.auto_save = start_auto_save(self.auto_save, self.current_file, self.code_editor)

    def open_last_edit_file(self):
        self.highlight_text.search()
        return open_last_edit_file(self.file_from_output_content, self.code_editor)

    def execute_program(self, event=None):
        if self.current_file is not None:
            save_file_then_can_run(self.current_file, self.code_editor)
        execute_code(self.current_file, self.save_file_to_open, self.exec_manager)

    def show_popup_menu(self, event):
        """
        :param event: tkinter event bind Button-3
        """
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
        :param use_theme: what theme editor used
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
        self.menu.add_command(
            label="Run",
            command=self.execute_program
        )
        self.menu.add_command(
            label="Run on shell",
            command=lambda: execute_shell_command(self.run_result, self.code_editor)
        )
        self.menu.add_command(
            label="Stop",
            command=lambda: stop_program(self.exec_manager)
        )
        # Text menu
        self.text_menu = tkinter.Menu(self.menu, tearoff=0)
        self.text_font_sub_menu = tkinter.Menu(self.text_menu, tearoff=0)
        self.text_size_sub_menu = tkinter.Menu(self.text_menu, tearoff=0)
        self.font_tuple = get_font(self.main_window)
        for i in range(len(self.font_tuple)):
            self.text_font_sub_menu.add_command(
                label=str(self.font_tuple[i]),
                command=lambda choose_font=self.font_tuple[i]: change_font(self.code_editor, self.run_result, choose_font)
            )
        for i in range(12, 36, 2):
            self.text_size_sub_menu.add_command(
                label=str(i),
                command=lambda font_size=i: change_font_size(self.code_editor, self.run_result, font_size)
            )
        self.text_menu.add_cascade(label="Font", menu=self.text_font_sub_menu)
        self.text_menu.add_cascade(label="Font Size", menu=self.text_size_sub_menu)
        # Encoding menu
        self.encoding_menu = tkinter.Menu(self.menu, tearoff=0)
        for i in range(len(encoding_list)):
            self.encoding_menu.add_command(
                label=str(encoding_list[i]),
                command=lambda choose_encoding=encoding_list[i]: set_encoding(self.exec_manager, choose_encoding)
            )
        # Language menu
        self.language_menu = tkinter.Menu(self.menu, tearoff=0)
        for i in range(len(language_list)):
            self.language_menu.add_command(
                label=str(language_list[i]),
                command=lambda choose_language=language_list[i]: set_language(self.exec_manager, choose_language)
            )
        # add and config
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.menu.add_cascade(label="Text", menu=self.text_menu)
        self.menu.add_cascade(label="Encoding", menu=self.encoding_menu)
        self.menu.add_cascade(label="Language", menu=self.language_menu)
        self.main_window.config(menu=self.menu)
        # Popup menu
        self.popup_menu = Menu(self.main_window, tearoff=0)
        self.popup_menu.add_command(
            label="Run",
            command=self.execute_program
        )
        self.popup_menu.add_command(
            label="Run on shell",
            command=lambda: execute_shell_command(self.run_result, self.code_editor)
        )
        self.popup_menu.add_separator()
        self.popup_menu.add_cascade(label="File", menu=self.file_menu)
        self.popup_menu.add_cascade(label="Text", menu=self.text_menu)
        self.popup_menu.add_cascade(label="Encoding", menu=self.encoding_menu)
        self.popup_menu.add_cascade(label="Language", menu=self.language_menu)
        self.main_window.bind("<Button-3>", self.show_popup_menu)
        # set resize
        self.code_edit_frame.columnconfigure(0, weight=1)
        self.code_edit_frame.rowconfigure(0, weight=1)
        self.run_result_frame.columnconfigure(0, weight=1)
        self.run_result_frame.rowconfigure(1, weight=1)
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.rowconfigure(0, weight=1)
        # Highlight word
        self.highlight_text = HighlightText(self.code_editor)
        # current file
        self.current_file = None
        # file to output content
        self.file_from_output_content = open_content_and_start()
        if self.file_from_output_content is not None:
            self.current_file = self.open_last_edit_file()
            self.highlight_text.search()
        # close event
        self.main_window.protocol("WM_DELETE_WINDOW", self.close_event)
        # bind
        self.main_window.bind("<Control-Key-o>", self.open_file_to_read)
        self.main_window.bind("<Control-Key-s>", self.save_file_to_open)
        self.main_window.bind(
            "<Control-Key-F5>",
            self.execute_program
        )
        self.main_window.bind(
            "<Control-Key-F6>",
            lambda bind_exec_shell_command: execute_shell_command(self.run_result, self.code_editor)
        )
        # is this test run?
        self.test_run = False
        # Auto save thread
        self.auto_save = None
        if self.current_file is not None:
            self.auto_save = start_auto_save(self.auto_save, self.current_file, self.code_editor)
        self.exec_manager = ExecManager(
            run_result=self.run_result,
            process_error_function=process_error_text,
            main_window=self.main_window,
            running_menu=self.menu
        )

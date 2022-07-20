import os
import sys
from tkinter import Menu
from tkinter import Text
from tkinter import Tk
from tkinter import ttk

from je_editor.ui.ui_event.auto_save.start_auto_save.start_auto_save import start_auto_save
from je_editor.ui.ui_event.change_font.change_font import change_font
from je_editor.ui.ui_event.change_font.change_font import change_font_size
from je_editor.ui.ui_event.clear_result.clear_result import clear_result_area
from je_editor.ui.ui_event.close.close_event import close_event
from je_editor.ui.ui_event.encoding.set_encoding import set_encoding
from je_editor.ui.ui_event.execute.execute_code.exec_code import execute_code
from je_editor.ui.ui_event.execute.execute_code.exec_code import stop_program
from je_editor.ui.ui_event.execute.execute_shell_command.run_on_shell import execute_shell_command
from je_editor.ui.ui_event.language.set_language import set_language
from je_editor.ui.ui_event.open_file.open_file_to_read.open_file_to_read import open_file_to_read
from je_editor.ui.ui_event.open_file.open_last_edit_file.open_last_edit_file import open_last_edit_file
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_then_can_run
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_to_open
from je_editor.ui.ui_event.tag_keyword.tag_keyword import HighlightText
from je_editor.ui.ui_event.text_process.program_exec.exec_text import ExecManager
from je_editor.ui.ui_event.text_process.program_exec.process_error import process_error_text
from je_editor.ui.ui_utils.editor_content.content_save import open_content_and_start
from je_editor.ui.ui_utils.editor_content.editor_data import editor_data_dict
from je_editor.ui.ui_utils.encoding.encoding_data_module import encoding_list
from je_editor.ui.ui_utils.font.font import get_font
from je_editor.ui.ui_utils.language.language_data_module import language_list
from je_editor.ui.ui_utils.language_data_module.language_compiler_data_module import language_compiler
from je_editor.ui.ui_utils.language_data_module.language_param_data_module import language_compiler_param
from je_editor.utils.exception.exceptions import JEditorContentFileException


class EditorMain(object):

    # start editor and start auto save if auto save not start
    def start_editor(self):
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        if self.debug_run:
            self.close_event()
        else:
            self.main_window.mainloop()

    # editor close event
    def close_event(self):
        editor_data_dict["last_file"] = self.current_file
        if self.file_from_output_content is not None:
            self.file_from_output_content["last_file"] = self.current_file
        close_event(self.main_window, self.exec_manager)

    # editor open file from path
    def ui_open_file_to_read(self, event=None):
        temp = open_file_to_read(self.code_editor_textarea)
        self.current_file = temp
        self.highlight_text.search()
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)

    # save editor file to choose path
    def ui_save_file_to_open(self, event=None):
        self.current_file = save_file_to_open(self.code_editor_textarea)
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)

    def ui_open_last_edit_file(self):
        self.highlight_text.search()
        return open_last_edit_file(self.file_from_output_content.get("last_file"), self.code_editor_textarea)

    def ui_execute_program(self, event=None):
        if self.current_file is not None:
            save_file_then_can_run(self.current_file, self.code_editor_textarea)
        execute_code(self.current_file, self.ui_save_file_to_open, self.exec_manager)

    def ui_show_popup_menu(self, event):
        """
        :param event: tkinter event bind Button-3
        """
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def ui_init(self):
        # Highlight word
        self.highlight_text = HighlightText(self.code_editor_textarea)
        # file from output content
        self.file_from_output_content = open_content_and_start()
        try:
            if self.file_from_output_content is not None:
                self.current_file = self.ui_open_last_edit_file()
                self.highlight_text.search()
                if self.file_from_output_content.get("theme") is not None:
                    self.highlight_text.theme = self.file_from_output_content.get("theme")
                    editor_data_dict["theme"] = self.file_from_output_content.get(
                        "theme")
                if self.file_from_output_content.get("language") is not None:
                    language_from_content = self.file_from_output_content.get("language")
                    for language in language_from_content:
                        if language not in language_list:
                            language_list.append(language)
                    set_language(self.exec_manager, language_from_content)
                if self.file_from_output_content.get("encoding") is not None:
                    set_encoding(self.exec_manager, self.file_from_output_content.get("encoding"))
                if self.file_from_output_content.get("font") is not None:
                    change_font(
                        self.code_editor_textarea,
                        self.program_run_result_textarea,
                        self.file_from_output_content.get("font")
                    )
                if self.file_from_output_content.get("font_size") is not None:
                    change_font_size(
                        self.code_editor_textarea,
                        self.program_run_result_textarea,
                        self.file_from_output_content.get("font_size")
                    )
                try:
                    if self.file_from_output_content.get("language_precompiler") is not None:
                        language_compiler.update(self.file_from_output_content.get("language_precompiler"))
                        editor_data_dict["language_precompiler"] = self.file_from_output_content.get(
                            "language_precompiler")
                    if self.file_from_output_content.get("language_compiler_param") is not None:
                        language_compiler_param.update(self.file_from_output_content.get("language_compiler_param"))
                        editor_data_dict["language_compiler_param"] = self.file_from_output_content.get(
                            "language_compiler_param")
                except JEditorContentFileException as error:
                    print(repr(error), file=sys.stderr)
                if self.file_from_output_content.get("tab_size") is not None:
                    editor_data_dict["tab_size"] = self.file_from_output_content.get(
                        "tab_size")
                    self.code_editor_textarea.config(tabs=self.file_from_output_content.get("tab_size"))
        except JEditorContentFileException as error:
            print(repr(error), file=sys.stderr)
        self.highlight_text.search()
        print("language_compiler_param: " + str(language_compiler_param))
        print("language_compiler: " + str(language_compiler))
        print("language_list: " + str(language_list))

    # default event
    def do_test(self, event=None):
        print(self.debug_run)

    def __init__(self, use_theme=None, debug=False, main_window=Tk()):
        """
        :param use_theme: what theme editor used
        :param main_window: Tk instance
        """
        os.environ["PYTHONUNBUFFERED"] = "1"
        # is this test run?
        self.debug_run = debug
        # Auto save thread
        self.auto_save_thread = None
        # current file
        self.current_file = None
        # style
        self.file_from_output_content = None
        self.highlight_text = None
        self.style = ttk.Style()
        if use_theme is not None:
            self.style.theme_use(use_theme)
        # set main window title and add main frame
        self.main_window = main_window
        self.main_window.title("je_editor")
        self.code_edit_frame = ttk.Frame(self.main_window, padding="3 3 12 12")
        self.program_run_result_frame = ttk.Frame(self.main_window, padding="3 3 12 12")
        # set code edit
        self.code_editor_textarea = Text(self.code_edit_frame, undo=True, autoseparators=True, maxundo=-1, wrap="none")
        self.code_editor_textarea.configure(state="normal")
        self.code_editor_textarea.config(tabs="1c")
        self.code_editor_textarea_scrollbar_y = ttk.Scrollbar(self.code_edit_frame, orient="vertical",
                                                              command=self.code_editor_textarea.yview)
        self.code_editor_textarea_scrollbar_x = ttk.Scrollbar(self.code_edit_frame, orient="horizontal",
                                                              command=self.code_editor_textarea.xview)
        self.code_editor_textarea["yscrollcommand"] = self.code_editor_textarea_scrollbar_y.set
        self.code_editor_textarea["xscrollcommand"] = self.code_editor_textarea_scrollbar_x.set
        # run result
        self.program_run_result_textarea = Text(self.program_run_result_frame, wrap="none")
        self.program_run_result_textarea_scrollbar_y = ttk.Scrollbar(self.program_run_result_frame, orient="vertical",
                                                                     command=self.program_run_result_textarea.yview)
        self.program_run_result_textarea_scrollbar_x = ttk.Scrollbar(self.program_run_result_frame, orient="horizontal",
                                                                     command=self.program_run_result_textarea.xview)
        self.program_run_result_textarea["yscrollcommand"] = self.program_run_result_textarea_scrollbar_y.set
        self.program_run_result_textarea["xscrollcommand"] = self.program_run_result_textarea_scrollbar_x.set
        # close event
        self.main_window.protocol("WM_DELETE_WINDOW", self.close_event)
        # bind
        self.main_window.bind("<Control-Key-o>", self.ui_open_file_to_read)
        self.main_window.bind("<Control-Key-s>", self.ui_save_file_to_open)
        self.main_window.bind(
            "<Control-Key-F5>",
            self.ui_execute_program
        )
        self.main_window.bind(
            "<Control-Key-F6>",
            lambda bind_exec_shell_command: execute_shell_command(self.program_run_result_textarea,
                                                                  self.code_editor_textarea)
        )
        # Menubar
        # Main menu
        self.menu = Menu(self.main_window)
        # File menu
        self.file_menu = Menu(self.menu, tearoff=0)
        # Text menu
        self.text_menu = Menu(self.menu, tearoff=0)
        self.text_font_sub_menu = Menu(self.text_menu, tearoff=0)
        self.text_size_sub_menu = Menu(self.text_menu, tearoff=0)
        self.font_tuple = get_font(self.main_window)
        self.text_menu.add_cascade(label="Font", menu=self.text_font_sub_menu)
        self.text_menu.add_cascade(label="Font Size", menu=self.text_size_sub_menu)
        # Encoding menu
        self.encoding_menu = Menu(self.menu, tearoff=0)
        # Language menu
        self.language_menu = Menu(self.menu, tearoff=0)
        if self.current_file is not None:
            self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        self.exec_manager = ExecManager(
            program_run_result_textarea=self.program_run_result_textarea,
            process_error_function=process_error_text,
            main_window=self.main_window,
            running_menu=self.menu
        )
        # ui init should before grid and menu init
        self.ui_init()
        # grid and menu set
        self.code_edit_frame.grid(column=0, row=0, sticky="nsew")
        self.program_run_result_frame.grid(column=0, row=1, sticky="nsew")
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_rowconfigure(1, weight=1)
        self.code_editor_textarea.grid(column=0, row=0, sticky="nsew")
        self.code_editor_textarea_scrollbar_y.grid(column=1, row=0, sticky="ns")
        self.code_editor_textarea_scrollbar_x.grid(column=0, row=2, sticky="nsew")
        self.program_run_result_textarea.grid(column=0, row=1, sticky="nsew")
        self.program_run_result_textarea_scrollbar_y.grid(column=1, row=1, sticky="ns")
        self.program_run_result_textarea_scrollbar_x.grid(column=0, row=3, sticky="nsew")
        # bind and config
        self.program_run_result_textarea.configure(state="disabled")
        self.program_run_result_textarea.bind("<1>", lambda event: self.program_run_result_textarea.focus_set())
        self.main_window.bind("<Button-3>", self.ui_show_popup_menu)
        # set resize
        self.code_edit_frame.columnconfigure(0, weight=1)
        self.code_edit_frame.rowconfigure(0, weight=1)
        self.program_run_result_frame.columnconfigure(0, weight=1)
        self.program_run_result_frame.rowconfigure(1, weight=1)
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.rowconfigure(0, weight=1)
        # menu add command
        # main menu bar
        self.menu.add_command(
            label="Run",
            command=self.ui_execute_program
        )
        self.menu.add_command(
            label="Run on shell",
            command=lambda: execute_shell_command(self.program_run_result_textarea, self.code_editor_textarea)
        )
        self.menu.add_command(
            label="Stop",
            command=lambda: stop_program(self.exec_manager)
        )
        self.file_menu.add_command(label="Save File", command=self.ui_save_file_to_open)
        self.file_menu.add_command(label="Open File", command=self.ui_open_file_to_read)
        # Encoding menu
        for i in range(len(encoding_list)):
            self.encoding_menu.add_command(
                label=str(encoding_list[i]),
                command=lambda choose_encoding=encoding_list[i]: set_encoding(self.exec_manager, choose_encoding)
            )
        # Font menu
        for i in range(len(self.font_tuple)):
            self.text_font_sub_menu.add_command(
                label=str(self.font_tuple[i]),
                command=lambda choose_font=self.font_tuple[i]:
                change_font(self.code_editor_textarea, self.program_run_result_textarea, choose_font)
            )
        # Text size menu
        for i in range(12, 36, 2):
            self.text_size_sub_menu.add_command(
                label=str(i),
                command=lambda font_size=i: change_font_size(self.code_editor_textarea,
                                                             self.program_run_result_textarea,
                                                             font_size)
            )
        # Language menu
        for i in range(len(language_list)):
            self.language_menu.add_command(
                label=str(language_list[i]),
                command=lambda choose_language=language_list[i]: set_language(self.exec_manager, choose_language)
            )
        # Popup menu
        self.popup_menu = Menu(self.main_window, tearoff=0)
        self.popup_menu.add_separator()
        self.popup_menu.add_cascade(label="File", menu=self.file_menu)
        self.popup_menu.add_cascade(label="Text", menu=self.text_menu)
        self.popup_menu.add_cascade(label="Encoding", menu=self.encoding_menu)
        self.popup_menu.add_cascade(label="Language", menu=self.language_menu)
        self.popup_menu.add_command(
            label="Run",
            command=self.ui_execute_program
        )
        self.popup_menu.add_command(
            label="Stop",
            command=lambda: stop_program(self.exec_manager)
        )
        self.popup_menu.add_command(
            label="Run on shell",
            command=lambda: execute_shell_command(self.program_run_result_textarea, self.code_editor_textarea)
        )
        self.popup_menu.add_command(
            label="Clean Result", command=lambda: clear_result_area(
                self.program_run_result_textarea
            )
        )
        # add and config
        self.menu.add_cascade(label="File", menu=self.file_menu)
        self.menu.add_cascade(label="Text", menu=self.text_menu)
        self.menu.add_cascade(label="Encoding", menu=self.encoding_menu)
        self.menu.add_cascade(label="Language", menu=self.language_menu)
        self.menu.add_cascade(
            label="Clean Result", command=lambda: clear_result_area(
                self.program_run_result_textarea
            )
        )
        self.main_window.config(menu=self.menu)

    def use_choose_theme(self, use_theme=None):
        self.style.theme_use(use_theme)


def start_editor(use_theme=None, **kwargs):
    new_editor = EditorMain(use_theme=use_theme, **kwargs)
    new_editor.start_editor()
    return new_editor

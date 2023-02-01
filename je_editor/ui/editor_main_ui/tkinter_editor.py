import os
from tkinter import Menu
from tkinter import Tk
from tkinter import ttk

from je_editor.utils.exception.exceptions import JEditorException
from je_editor.ui.editor_main_ui.content_init.content_init import content_init
from je_editor.ui.editor_main_ui.menu.build_menu import build_menu
from je_editor.ui.editor_main_ui.menu.file_menu.build_file_menu import build_file_menu
from je_editor.ui.editor_main_ui.menu.popup_menu.build_popup_menu import build_popup_menu
from je_editor.ui.editor_main_ui.menu.run_menu.build_run_menu import build_run_menu
from je_editor.ui.editor_main_ui.protocal_setting.set_ui_protocol import tkinter_set_protocol
from je_editor.ui.editor_main_ui.redirect_output.redirect_output_to_tkinter_ui import redirect_output
from je_editor.ui.editor_main_ui.ui_event_bind.event_bind import tkinter_event_bind
from je_editor.ui.editor_main_ui.ui_grid.build_ui_grid import build_grid
from je_editor.ui.editor_main_ui.ui_setting.ui_setting import tkinter_ui_setting
from je_editor.ui.ui_event.auto_save.start_auto_save.start_auto_save import start_auto_save
from je_editor.ui.ui_event.close.close_event import close_event
from je_editor.ui.ui_event.execute.execute_code.exec_code import execute_code
from je_editor.ui.ui_event.open_file.open_file_to_read.open_file_to_read import open_file_to_read
from je_editor.ui.ui_event.open_file.open_last_edit_file.open_last_edit_file import open_last_edit_file
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_then_can_run
from je_editor.ui.ui_event.save_file.save_file_to_open.save_file_to_open import save_file_to_open
from je_editor.ui.ui_event.text_process.program_exec.code_exec_manager import ExecManager
from je_editor.ui.ui_event.text_process.program_exec.process_error import process_error_text
from je_editor.ui.ui_event.text_process.shell.shell_exec_manager import ShellManager
from je_editor.utils.editor_content.editor_content_data import editor_content_data_dict
from je_editor.utils.exception.exception_tags import je_editor_init_exec_manager_exception
from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance


class EditorMain(object):

    # start editor and start auto save if auto save not start
    def start_editor(self):
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        if self.debug_run:
            self.close_event()
        else:
            self.main_window.mainloop()

    def before_close_event(self):
        editor_content_data_dict["last_file"] = self.current_file
        if self.file_from_output_content is not None:
            self.file_from_output_content["last_file"] = self.current_file

    # editor close event
    def close_event(self):
        self.before_close_event()
        close_event(self.main_window, self.exec_manager)

    # editor open file from path
    def ui_open_file_to_read(self, event=None):
        temp = open_file_to_read(self.code_editor_textarea)
        self.current_file = temp
        self.highlight_text.search()
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        editor_content_data_dict["last_file"] = self.current_file

    # save editor file to choose path
    def ui_save_file_to_open(self, event=None):
        self.current_file = save_file_to_open(self.code_editor_textarea)
        self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        editor_content_data_dict["last_file"] = self.current_file

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

    # default event
    def do_test(self, event=None):
        print(self.debug_run)

    def __init__(self, use_theme=None, debug=False, main_window=Tk()):
        """
        :param use_theme: what theme editor used
        :param main_window: Tk instance
        """
        # ui param
        self.popup_menu = None
        self.program_run_result_textarea = None
        self.code_editor_textarea = None
        self.main_window = None
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
        tkinter_ui_setting(self, main_window)
        tkinter_set_protocol(self)
        # Menubar
        # Main menu
        self.menu = Menu(self.main_window)
        if self.current_file is not None:
            self.auto_save_thread = start_auto_save(self.auto_save_thread, self.current_file, self.code_editor_textarea)
        if self.program_run_result_textarea is None or self.main_window is None:
            raise JEditorException(je_editor_init_exec_manager_exception)
        else:
            self.exec_manager = ExecManager(
                program_run_result_textarea=self.program_run_result_textarea,
                process_error_function=process_error_text,
                main_window=self.main_window,
            )
            self.shell_manager = ShellManager(
                run_shell_result_textarea=self.program_run_result_textarea,
                process_error_function=process_error_text,
                main_window=self.main_window,
            )
        # ui init should before grid and menu init
        content_init(self)
        build_grid(self)
        tkinter_event_bind(self)
        # menu add command
        # main menu bar
        build_run_menu(self)
        build_file_menu(self)
        build_popup_menu(self)
        build_menu(self)
        redirect_manager_instance.set_redirect(self, True)
        self.program_run_result_textarea.after(10, lambda: redirect_output(self))

    def use_choose_theme(self, use_theme=None):
        self.style.theme_use(use_theme)


def start_editor(use_theme=None, **kwargs):
    new_editor = EditorMain(use_theme=use_theme, **kwargs)
    new_editor.start_editor()
    return new_editor

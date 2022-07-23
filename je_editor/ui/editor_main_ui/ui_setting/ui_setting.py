from tkinter import ttk, Text, Tk


def tkinter_ui_setting(editor_instance, main_window: Tk):
    # set main window title and add main frame
    editor_instance.main_window = main_window
    editor_instance.main_window.title("je_editor")
    editor_instance.code_edit_frame = ttk.Frame(editor_instance.main_window, padding="3 3 12 12")
    editor_instance.program_run_result_frame = ttk.Frame(editor_instance.main_window, padding="3 3 12 12")
    # set code edit
    editor_instance.code_editor_textarea = Text(
        editor_instance.code_edit_frame, undo=True, autoseparators=True, maxundo=-1, wrap="none")
    editor_instance.code_editor_textarea.configure(state="normal")
    editor_instance.code_editor_textarea.config(tabs="1c")
    editor_instance.code_editor_textarea_scrollbar_y = ttk.Scrollbar(
        editor_instance.code_edit_frame, orient="vertical",
        command=editor_instance.code_editor_textarea.yview
    )
    editor_instance.code_editor_textarea_scrollbar_x = ttk.Scrollbar(
        editor_instance.code_edit_frame, orient="horizontal",
        command=editor_instance.code_editor_textarea.xview)
    editor_instance.code_editor_textarea["yscrollcommand"] = editor_instance.code_editor_textarea_scrollbar_y.set
    editor_instance.code_editor_textarea["xscrollcommand"] = editor_instance.code_editor_textarea_scrollbar_x.set
    # run result
    editor_instance.program_run_result_textarea = Text(editor_instance.program_run_result_frame, wrap="none")
    editor_instance.program_run_result_textarea_scrollbar_y = ttk.Scrollbar(
        editor_instance.program_run_result_frame, orient="vertical",
        command=editor_instance.program_run_result_textarea.yview)
    editor_instance.program_run_result_textarea_scrollbar_x = ttk.Scrollbar(
        editor_instance.program_run_result_frame, orient="horizontal",
        command=editor_instance.program_run_result_textarea.xview)
    editor_instance.program_run_result_textarea[
        "yscrollcommand"] = editor_instance.program_run_result_textarea_scrollbar_y.set
    editor_instance.program_run_result_textarea[
        "xscrollcommand"] = editor_instance.program_run_result_textarea_scrollbar_x.set
    editor_instance.program_run_result_textarea.configure(state="disabled")

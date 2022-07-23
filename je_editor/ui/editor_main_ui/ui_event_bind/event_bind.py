from je_editor.ui.ui_event.execute.execute_shell_command.run_on_shell import execute_shell_command


def tkinter_event_bind(editor_instance):
    # bind
    editor_instance.program_run_result_textarea.bind(
        "<1>",
        lambda event: editor_instance.program_run_result_textarea.focus_set()
    )
    editor_instance.main_window.bind("<Button-3>", editor_instance.ui_show_popup_menu)
    editor_instance.main_window.bind("<Control-Key-o>", editor_instance.ui_open_file_to_read)
    editor_instance.main_window.bind("<Control-Key-s>", editor_instance.ui_save_file_to_open)
    editor_instance.main_window.bind(
        "<Control-Key-F5>",
        editor_instance.ui_execute_program
    )
    editor_instance.main_window.bind(
        "<Control-Key-F6>",
        lambda bind_exec_shell_command: execute_shell_command(editor_instance.program_run_result_textarea,
                                                              editor_instance.code_editor_textarea)
    )

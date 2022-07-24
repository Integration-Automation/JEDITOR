def build_grid(editor_instance):
    # grid and menu set
    editor_instance.code_edit_frame.grid(column=0, row=0, sticky="nsew")
    editor_instance.program_run_result_frame.grid(column=0, row=1, sticky="nsew")
    editor_instance.main_window.grid_rowconfigure(0, weight=1)
    editor_instance.main_window.grid_rowconfigure(1, weight=1)
    editor_instance.code_editor_textarea.grid(column=0, row=0, sticky="nsew")
    editor_instance.code_editor_textarea_scrollbar_y.grid(column=1, row=0, sticky="ns")
    editor_instance.code_editor_textarea_scrollbar_x.grid(column=0, row=2, sticky="nsew")
    editor_instance.program_run_result_textarea.grid(column=0, row=1, sticky="nsew")
    editor_instance.program_run_result_textarea_scrollbar_y.grid(column=1, row=1, sticky="ns")
    editor_instance.program_run_result_textarea_scrollbar_x.grid(column=0, row=3, sticky="nsew")
    # set resize
    editor_instance.code_edit_frame.columnconfigure(0, weight=1)
    editor_instance.code_edit_frame.rowconfigure(0, weight=1)
    editor_instance.program_run_result_frame.columnconfigure(0, weight=1)
    editor_instance.program_run_result_frame.rowconfigure(1, weight=1)
    editor_instance.main_window.columnconfigure(0, weight=1)
    editor_instance.main_window.rowconfigure(0, weight=1)

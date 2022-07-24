def build_menu(editor_instance):
    # add and config
    editor_instance.menu.add_cascade(label="Run", menu=editor_instance.run_menu)
    editor_instance.menu.add_cascade(label="File", menu=editor_instance.file_menu)
    editor_instance.main_window.config(menu=editor_instance.menu)

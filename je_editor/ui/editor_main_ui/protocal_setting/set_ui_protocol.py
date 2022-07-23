def tkinter_set_protocol(editor_instance):
    # close event
    editor_instance.main_window.protocol("WM_DELETE_WINDOW", editor_instance.close_event)

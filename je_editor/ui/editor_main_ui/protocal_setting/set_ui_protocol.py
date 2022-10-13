def tkinter_set_protocol(editor_instance):
    """
    use to init (set tkinter ui protocol)
    :param editor_instance: editor's instance
    :return: None
    """
    # close event
    editor_instance.main_window.protocol("WM_DELETE_WINDOW", editor_instance.close_event)

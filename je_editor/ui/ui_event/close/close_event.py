from je_editor.utils.editor_content.content_save import save_content_and_quit


def close_event(check_current_file, tkinter_window):
    """
    :param check_current_file: check have current file? if have; save and quit else only quit
    :param tkinter_window: the tkinter window will close
    :return: no return value
    """
    if check_current_file is not None:
        save_content_and_quit(check_current_file)
    tkinter_window.destroy()

from je_editor.ui.ui_utils.editor_content.content_save import save_content_and_quit


def close_event(tkinter_window, exec_manager):
    """
    :param exec_manager:
    :param tkinter_window: the tkinter window will close
    :return: no return value
    """
    save_content_and_quit()
    exec_manager.exit_program()
    tkinter_window.destroy()

from tkinter import NORMAL, END, DISABLED

from je_editor.utils.redirect_manager.redirect_manager_class import redirect_manager_instance


def redirect_output(editor_instance):
    """
    use to init
    :param editor_instance: editor's instance
    :return: None
    """
    editor_instance.program_run_result_textarea.configure(state=NORMAL)
    if not redirect_manager_instance.std_out_queue.empty():
        editor_instance.program_run_result_textarea.insert(
            END,
            redirect_manager_instance.std_out_queue.get_nowait(),
        )
    if not redirect_manager_instance.std_err_queue.empty():
        editor_instance.program_run_result_textarea.tag_configure("warning", foreground="red")
        editor_instance.program_run_result_textarea.insert(
            END,
            redirect_manager_instance.std_err_queue.get_nowait(),
            "warning",
        )
    editor_instance.program_run_result_textarea.configure(state=DISABLED)
    editor_instance.program_run_result_textarea.after(10, lambda: redirect_output(editor_instance))

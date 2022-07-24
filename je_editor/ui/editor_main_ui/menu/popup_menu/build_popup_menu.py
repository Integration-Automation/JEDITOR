from tkinter import Menu


def build_popup_menu(editor_instance):
    # Popup menu
    editor_instance.popup_menu = Menu(editor_instance.main_window, tearoff=0)
    editor_instance.popup_menu.add_cascade(label="File", menu=editor_instance.file_menu)
    editor_instance.popup_menu.add_cascade(label="Run", menu=editor_instance.run_menu)

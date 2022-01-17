from tkinter import END


def process_error_text(tkinter_text, error_text):
    """
    :param tkinter_text: tkinter textarea widget
    :param error_text: error text insert in to tkinter_text
    """
    tkinter_text.tag_configure("warning", foreground="red")
    tkinter_text.insert(END, error_text, "warning", "\n")

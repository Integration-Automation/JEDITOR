from tkinter import END


def process_error_text(tkinter_text, error_text):
    tkinter_text.tag_remove("warning", "1.0", END)
    tkinter_text.tag_configure("warning", foreground="red")
    tkinter_text.insert(END, error_text, "warning", "\n")

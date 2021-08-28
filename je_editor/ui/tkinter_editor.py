from tkinter import *
from tkinter import ttk

from je_editor.utils.code_tag.tag_word import Highlight


class editor_main(object):

    def __init__(self, main_window=Tk()):
        """
        :param main_window: Tk instance
        """
        # set main window title and add main frame
        self.main_window = main_window
        self.main_window.title("je_editor")
        self.main_frame = ttk.Frame(self.main_window, padding="3 3 12 12")
        self.main_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        # set code edit
        self.code_editor = Text(self.main_frame)
        self.scrollbar_x = ttk.Scrollbar(orient="horizontal", command=self.code_editor.xview)
        self.scrollbar_y = ttk.Scrollbar(orient="vertical", command=self.code_editor.yview)
        self.code_editor["xscrollcommand"] = self.scrollbar_x.set
        self.code_editor["yscrollcommand"] = self.scrollbar_y.set
        self.code_editor.grid(column=0, row=0, sticky=(N, W, E, S))
        self.scrollbar_x.grid(column=0, row=1)
        self.scrollbar_y.grid(column=1, row=0)
        word_list = ["print", "int"]
        Highlight(self.code_editor, word_list)
        # set resize
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.rowconfigure(0, weight=1)

    def start_editor(self):
        self.main_window.mainloop()

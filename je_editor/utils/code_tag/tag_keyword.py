from je_editor.utils.code_tag.keyword_list import keyword_list
from je_editor.utils.theme.theme import Theme
from tkinter import IntVar

class HighlightText(object):

    def __init__(self, tkinter_text, start_position="1.0", end_position="end"):
        self.tkinter_text = tkinter_text
        self.start_position = start_position
        self.end_position = end_position
        self.theme = Theme()
        self.tkinter_text.regexp = True
        self.tkinter_text.bind("<KeyRelease>", self.search)

    def search(self, event):
        tag = "temp"
        for tag in self.tkinter_text.tag_names():
            self.tkinter_text.tag_remove(tag, self.start_position, self.end_position)
        count_var = IntVar()
        for word in keyword_list:
            position = '1.0'
            self.tkinter_text.tag_config(word, foreground=self.theme.tag_keyword_color)
            while self.tkinter_text.compare(position, "<", "end"):
                find_function_index = self.tkinter_text.search("\m" + word + "\M", position, self.end_position, count=count_var, regexp=True)
                if not find_function_index:
                    break
                position = '{}+{}c'.format(find_function_index, len(word))
                self.tkinter_text.tag_add(tag, find_function_index, position)

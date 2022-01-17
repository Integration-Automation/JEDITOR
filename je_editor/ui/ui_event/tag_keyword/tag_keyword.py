from tkinter import IntVar

from je_editor.ui.ui_utils.keyword.keyword_list import keyword_list
from je_editor.ui.ui_utils.theme.theme import theme_dict


class HighlightText(object):

    def __init__(self, tkinter_text, start_position="1.0", end_position="end"):
        """
        :param tkinter_text: want to set highlight's tkinter text
        :param start_position: search start position
        :param end_position: search end position
        """
        self.tkinter_text = tkinter_text
        self.start_position = start_position
        self.end_position = end_position
        # theme dict on theme
        self.theme = theme_dict
        # use regexp
        self.tkinter_text.regexp = True
        # bind to keyboard key release
        self.tkinter_text.bind("<KeyRelease>", self.search)

    def search(self, event=None):
        """
        :param event: tkinter event
        create temp var tag
        remove tag
        search all word in keyword_list and tag
        """
        tag = "temp"
        for tag in self.tkinter_text.tag_names():
            self.tkinter_text.tag_remove(tag, self.start_position, self.end_position)
        count_var = IntVar()
        for word in keyword_list:
            position = '1.0'
            self.tkinter_text.tag_config(word, foreground=self.theme.get("tag_keyword_color"))
            while self.tkinter_text.compare(position, "<", "end"):
                find_function_index = self.tkinter_text.search(
                    "\m" + word + "\M",
                    position, self.end_position,
                    count=count_var,
                    regexp=True
                )
                if not find_function_index:
                    break
                position = '{}+{}c'.format(find_function_index, len(word))
                self.tkinter_text.tag_add(tag, find_function_index, position)

from je_editor.utils.code_tag.keyword_list import keyword_list
from je_editor.utils.theme.theme import Theme


class HighlightText(object):

    def __init__(self, tkinter_text, start_position="1.0", end_position="end"):
        self.tkinter_text = tkinter_text
        self.start_position = start_position
        self.end_position = end_position
        self.theme = Theme()
        self.tkinter_text.regexp = True
        self.tkinter_text.bind("<KeyRelease>", self.search)

    def search(self, event):
        position = '1.0'
        for word in keyword_list:
            self.tkinter_text.tag_config(word, foreground=self.theme.tag_keyword_color)
            while True:
                find_function_index = self.tkinter_text.search("\y" + word + "\y", position, self.end_position, regexp=True)
                if not find_function_index:
                    break
                position = '{}+{}c'.format(find_function_index, len(word))
                self.tkinter_text.tag_add(word, find_function_index, position)

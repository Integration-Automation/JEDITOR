from je_editor.utils.theme.theme import Theme


class HighlightText(object):

    def __init__(self, tkinter_text, word_list, start_position="1.0", end_position="end"):
        self.tkinter_text = tkinter_text
        self.word_list = word_list
        self.start_position = start_position
        self.end_position = end_position
        self.theme = Theme()
        self.tkinter_text.regexp = True
        self.tkinter_text.bind("<KeyRelease>", self.search)
        for word in word_list:
            self.tkinter_text.tag_config(word, foreground=self.theme.tag_word_color)

    def search(self, event):
        position = '1.0'
        for word in self.word_list:
            while True:
                find_word_index = self.tkinter_text.search("\m" + word + "\M", position, self.end_position, regexp=True)
                if not find_word_index:
                    break
                position = '{}+{}c'.format(find_word_index, len(word))
                self.tkinter_text.tag_add(word, find_word_index, position)

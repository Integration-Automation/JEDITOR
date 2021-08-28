from je_editor.utils.theme.theme import white_theme_tag_word_foreground_color


class Highlight(object):

    def __init__(self, tkinter_text, word_list, start_position="1.0", end_position="end-1c"):
        self.tkinter_text = tkinter_text
        self.word_list = word_list
        self.start_position = start_position
        self.end_position = end_position
        self.tkinter_text.bind("<KeyRelease>", self.editor_key_release_event)
        for word in range(len(self.word_list)):
            self.tkinter_text.tag_config(self.word_list[word], foreground=white_theme_tag_word_foreground_color)

    def editor_key_release_event(self, event):
        for word in range(len(self.word_list)):
            find_word = self.tkinter_text.search(self.word_list[word], self.start_position, self.end_position)
            # not found
            if not find_word:
                break
            position = "{}+{}c".format(find_word, len(self.word_list[word]))
            self.tkinter_text.tag_add(self.word_list[word], self.start_position, position)



from tkinter import Text
from tkinter import Tk

from je_editor.utils.font.font import create_new_font
from je_editor.utils.font.font import get_font

test_root = Tk()
font_list = get_font(test_root)
print(font_list)
print(type(font_list))
test_font = create_new_font("System")
print(test_font)
test_text = Text(test_root)
test_text.configure(font=test_font)

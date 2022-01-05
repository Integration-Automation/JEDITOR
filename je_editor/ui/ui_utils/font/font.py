from tkinter import font
from tkinter.font import Font


def get_font(root, **kwargs):
    return font.families(root, **kwargs)


def create_new_font(font_family: str, font_size: int = 12, **kwargs):
    new_font = Font(font=(font_family, font_size), **kwargs)
    return new_font

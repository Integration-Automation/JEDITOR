from tkinter import font
from tkinter.font import Font


def get_font(root, **kwargs):
    """
    :param root: get current font families
    :param kwargs: another param
    """
    return font.families(root, **kwargs)


def create_new_font(font_family: str, font_size: int = 12, **kwargs):
    """
    :param font_family: which font family choose to create new font
    :param font_size: font size
    :param kwargs:  another param
    """
    new_font = Font(font=(font_family, font_size), **kwargs)
    return new_font

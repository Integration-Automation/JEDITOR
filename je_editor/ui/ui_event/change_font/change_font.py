from je_editor.ui.ui_utils.font.font import create_new_font
from tkinter.font import Font


def _config_change(tkinter_text_area, run_result, new_font):
    """
    :param tkinter_text_area: textarea who change font
    :param run_result: text area who change font
    :param new_font: which font chose
    """
    tkinter_text_area.configure(font=new_font)
    run_result.configure(font=new_font)


def change_font(tkinter_text_area, run_result, tkinter_font: str):
    """
    :param tkinter_text_area: which textarea change font
    :param run_result: which textarea change font
    :param tkinter_font: which font chose
    """
    current_font_size = Font(font=tkinter_text_area["font"]).actual()["size"]
    new_font = create_new_font(tkinter_font, font_size=current_font_size)
    _config_change(tkinter_text_area, run_result, new_font)


def change_font_size(tkinter_text_area, run_result, font_size: int):
    """
    :param tkinter_text_area: which  textarea change font
    :param run_result: which  textarea change font
    :param font_size:which font size choose
    """
    current_font_family = Font(font=tkinter_text_area["font"]).actual()["family"]
    new_font = create_new_font(current_font_family, font_size=font_size)
    _config_change(tkinter_text_area, run_result, new_font)

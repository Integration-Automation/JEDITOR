from je_editor.ui.ui_utils.font.font import create_new_font
from tkinter.font import Font


def change_font(tkinter_text_area, run_result, tkinter_font: str):
    current_font_size = Font(font=tkinter_text_area["font"]).actual()["size"]
    new_font = create_new_font(tkinter_font, font_size=current_font_size)
    tkinter_text_area.configure(font=new_font)
    run_result.configure(font=new_font)


def change_font_size(tkinter_text_area, run_result, font_size: int):
    new_font = Font(font=tkinter_text_area["font"]).actual()["family"]
    new_font = create_new_font(new_font, font_size=font_size)
    tkinter_text_area.configure(font=new_font)
    run_result.configure(font=new_font)

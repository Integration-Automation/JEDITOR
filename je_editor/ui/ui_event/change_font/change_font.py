from je_editor.ui.ui_utils.font.font import create_new_font


def change_font(tkinter_text_area, tkinter_font: str):
    new_font = create_new_font(tkinter_font, font_size=12)
    tkinter_text_area.configure(font=new_font)


def change_font_size(tkinter_text_area, font_size: int):
    new_font = tkinter_text_area["font"]
    new_font = create_new_font(new_font, font_size=font_size)
    tkinter_text_area.configure(font=new_font)

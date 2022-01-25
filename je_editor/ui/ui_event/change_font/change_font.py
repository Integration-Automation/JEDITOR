from je_editor.ui.ui_utils.font.font import create_new_font
from je_editor.ui.ui_utils.editor_content.editor_data import editor_data_dict
from tkinter.font import Font


def _config_change(program_run_result_textarea, shell_run_result_textarea, new_font):
    """
    :param program_run_result_textarea: textarea who change font
    :param shell_run_result_textarea: text area who change font
    :param new_font: which font chose
    """
    program_run_result_textarea.configure(font=new_font)
    shell_run_result_textarea.configure(font=new_font)


def change_font(program_run_result_textarea, shell_run_result_textarea, tkinter_font: str):
    """
    :param program_run_result_textarea: which textarea change font
    :param shell_run_result_textarea: which textarea change font
    :param tkinter_font: which font chose
    """
    current_font_size = Font(font=program_run_result_textarea["font"]).actual()["size"]
    new_font = create_new_font(tkinter_font, font_size=current_font_size)
    _config_change(program_run_result_textarea, shell_run_result_textarea, new_font)
    editor_data_dict["font"] = tkinter_font


def change_font_size(program_run_result_textarea, shell_run_result_textarea, font_size: int):
    """
    :param program_run_result_textarea: which  textarea change font
    :param shell_run_result_textarea: which  textarea change font
    :param font_size:which font size choose
    """
    current_font_family = Font(font=program_run_result_textarea["font"]).actual()["family"]
    new_font = create_new_font(current_font_family, font_size=font_size)
    _config_change(program_run_result_textarea, shell_run_result_textarea, new_font)
    editor_data_dict["font_size"] = font_size

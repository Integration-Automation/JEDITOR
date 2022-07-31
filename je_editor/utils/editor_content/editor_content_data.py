from je_editor.utils.theme.theme import theme_dict


"""
if you are using python3
language_precompiler and language_compiler_param value None is right
if you want to add param you can edit language_compiler_param
"""

editor_content_data_dict = {
    "last_file": None,
    "theme": theme_dict,
    "language": ["python3", "python"],
    "language_precompiler": None,
    "language_compiler_param": None,
    "encoding": "utf-8",
    "font": "TkDefaultFont",
    "font_size": 12,
    "tab_size": "1c",
    "program_buffer": 10240000,
}

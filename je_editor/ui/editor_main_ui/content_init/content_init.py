import sys

from je_editor.ui.ui_event.change_font.change_font import change_font, change_font_size
from je_editor.ui.ui_event.encoding.set_encoding import set_encoding
from je_editor.ui.ui_event.language.set_language import set_language
from je_editor.ui.ui_event.tag_keyword.tag_keyword import HighlightText
from je_editor.utils.editor_content.content_save import open_content_and_start
from je_editor.utils.editor_content.editor_content_data import editor_content_data_dict
from je_editor.utils.exception.exceptions import JEditorContentFileException
from je_editor.utils.language.language_data_module import language_list
from je_editor.utils.language_data_module.language_compiler_data_module import language_compiler
from je_editor.utils.language_data_module.language_param_data_module import language_compiler_param


def content_init(editor_instance):
    """
    use to init (read data and set data)
    :param editor_instance: editor's instance
    :return: None
    """
    # Highlight word
    editor_instance.highlight_text = HighlightText(editor_instance.code_editor_textarea)
    # file from output content
    editor_instance.file_from_output_content = open_content_and_start()
    try:
        if editor_instance.file_from_output_content is not None:
            editor_instance.highlight_text.search()
            if editor_instance.file_from_output_content.get("last_file") is not None:
                last_file = editor_instance.file_from_output_content.get("last_file")
                editor_content_data_dict["last_file"] = last_file
                editor_instance.current_file = editor_instance.ui_open_last_edit_file()
            if editor_instance.file_from_output_content.get("theme") is not None:
                editor_instance.highlight_text.theme = editor_instance.file_from_output_content.get("theme")
                editor_content_data_dict["theme"] = editor_instance.file_from_output_content.get(
                    "theme")
            if editor_instance.file_from_output_content.get("language") is not None:
                language_from_content = editor_instance.file_from_output_content.get("language")
                for language in language_from_content:
                    if language not in language_list:
                        language_list.append(language)
                set_language(editor_instance.exec_manager, language_from_content)
            if editor_instance.file_from_output_content.get("encoding") is not None:
                set_encoding(editor_instance.exec_manager, editor_instance.file_from_output_content.get("encoding"))
            if editor_instance.file_from_output_content.get("font") is not None:
                change_font(
                    editor_instance.code_editor_textarea,
                    editor_instance.program_run_result_textarea,
                    editor_instance.file_from_output_content.get("font")
                )
            if editor_instance.file_from_output_content.get("font_size") is not None:
                change_font_size(
                    editor_instance.code_editor_textarea,
                    editor_instance.program_run_result_textarea,
                    editor_instance.file_from_output_content.get("font_size")
                )
            try:
                if editor_instance.file_from_output_content.get("language_precompiler") is not None:
                    language_compiler.update(editor_instance.file_from_output_content.get("language_precompiler"))
                    editor_content_data_dict["language_precompiler"] = editor_instance.file_from_output_content.get(
                        "language_precompiler")
                if editor_instance.file_from_output_content.get("language_compiler_param") is not None:
                    language_compiler_param.update(editor_instance.file_from_output_content.get(
                        "language_compiler_param"))
                    editor_content_data_dict["language_compiler_param"] = editor_instance.file_from_output_content.get(
                        "language_compiler_param")
            except JEditorContentFileException as error:
                print(repr(error), file=sys.stderr)
            if editor_instance.file_from_output_content.get("tab_size") is not None:
                editor_content_data_dict["tab_size"] = editor_instance.file_from_output_content.get(
                    "tab_size")
                editor_instance.code_editor_textarea.config(
                    tabs=editor_instance.file_from_output_content.get("tab_size"))
            if editor_instance.file_from_output_content.get("program_buffer") is not None:
                editor_content_data_dict["program_buffer"] = editor_instance.file_from_output_content.get(
                    "program_buffer")
                editor_instance.exec_manager.program_buffer = int(editor_content_data_dict["program_buffer"])

    except JEditorContentFileException as error:
        print(repr(error), file=sys.stderr)
    editor_instance.highlight_text.search()

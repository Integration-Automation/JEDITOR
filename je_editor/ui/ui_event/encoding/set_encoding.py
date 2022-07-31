from je_editor.utils.editor_content.editor_content_data import editor_content_data_dict


def set_encoding(exec_manager, encoding):
    """
    :param exec_manager: which program exec manage change encoding
    :param encoding: which encoding choose
    """
    exec_manager.program_encoding = encoding
    editor_content_data_dict["encoding"] = encoding

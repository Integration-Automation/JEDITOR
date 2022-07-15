from je_editor.ui.ui_utils.editor_content.editor_data import editor_data_dict


def set_language(exec_manager, language):
    """
    :param exec_manager: which exec manager change program language
    :param language: set exec manager program language
    """
    if type(language) is list:
        exec_manager.program_language = language[0]
    else:
        exec_manager.program_language = language
    editor_data_dict["language"] = language

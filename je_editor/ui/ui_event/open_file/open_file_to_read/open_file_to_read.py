from je_editor.utils.file.open.open_file import open_file


def open_file_to_read(code_editor):
    """
    :param code_editor the editor to insert file content
    :return readied file
    show open file dialog
    if choose some file
        open and read it insert content to tkinter code_editor
        change current file
        start auto save
    """
    temp_to_check_file = open_file()
    if temp_to_check_file is not None and temp_to_check_file != "":
        code_editor.delete("1.0", "end-1c")
        code_editor.insert("end-1c", temp_to_check_file[1])
        return temp_to_check_file[0]
    else:
        return None

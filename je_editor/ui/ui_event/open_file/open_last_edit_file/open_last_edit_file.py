from je_editor.utils.file.open.open_file import read_file


def open_last_edit_file(file_from_output_content, code_editor):
    """
    :param file_from_output_content: readied file from output content
    :param code_editor the editor to insert file content
    :return readied file
    open last edit file
    if success open file
    insert file content to code_editor
    """
    temp_to_check_file = read_file(file_from_output_content)
    if temp_to_check_file is not None:
        code_editor.delete("1.0", "end-1c")
        code_editor.insert("end-1c", temp_to_check_file[1])
        return temp_to_check_file[0]

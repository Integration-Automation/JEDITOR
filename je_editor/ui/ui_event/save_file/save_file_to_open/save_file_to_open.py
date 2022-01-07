from je_editor.utils.file.save.save_file import save_file
from je_editor.utils.file.save.save_file import write_file


def save_file_to_open(code_editor):
    """
    :return saved file
    show save file dialog
    if saved
        change current file to new file
        start auto save
    """
    temp_to_check_file = save_file(code_editor.get("1.0", "end-1c"))
    if temp_to_check_file is not None and temp_to_check_file != "":
        return temp_to_check_file


def save_file_then_can_run(file, code_editor):
    write_file(file, code_editor.get("1.0", "end-1c"))


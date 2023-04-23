import os

from PySide6.QtWidgets import QFileDialog

from je_editor.utils.file.save.save_file import write_file


def choose_file_get_save_filename(parent_qt_instance):
    filename, file_filter = QFileDialog().getSaveFileName(
        parent=parent_qt_instance,
        dir=os.getcwd()
    )
    if filename is not None and filename != "":
        parent_qt_instance.current_file = filename
        write_file(filename, parent_qt_instance.code_edit.toPlainText())

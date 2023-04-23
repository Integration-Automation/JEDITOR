import os

from PySide6.QtWidgets import QFileDialog

from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_filename(parent_qt_instance):
    filename = QFileDialog().getOpenFileName(
        parent=parent_qt_instance,
        dir=os.getcwd()
    )[0]
    if filename is not None and filename != "":
        parent_qt_instance.current_file = filename
        file, file_content = read_file(filename)
        parent_qt_instance.code_edit.setPlainText(
            file_content
            )
        if parent_qt_instance.auto_save_thread is not None:
            parent_qt_instance.auto_save_thread.file = parent_qt_instance.current_file

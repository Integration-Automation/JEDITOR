import os

from PySide6.QtWidgets import QFileDialog


def choose_file_get_open_filename(parent_qt_instance):
    filename, file_filter = QFileDialog().getOpenFileName(
        parent=parent_qt_instance,
        dir=os.getcwd()
    )
    if filename is not None:
        parent_qt_instance.current_file = filename
        print(parent_qt_instance.current_file)

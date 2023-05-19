import os

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.auto_save.auto_save_thread import SaveThread
from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_filename(parent_qt_instance):
    """
    Open file and set code edit content
    :param parent_qt_instance: Pyside parent
    :return: None
    """
    filename = QFileDialog().getOpenFileName(
        parent=parent_qt_instance,
        dir=os.getcwd()
    )[0]
    if filename is not None and filename != "":
        parent_qt_instance.current_file = filename
        file_content = read_file(filename)[1]
        parent_qt_instance.code_edit.setPlainText(
            file_content
            )
        if parent_qt_instance.auto_save_thread is None:
            parent_qt_instance.auto_save_thread = SaveThread(
                parent_qt_instance.current_file,
                parent_qt_instance.code_edit.toPlainText()
            )
            parent_qt_instance.auto_save_thread.start()
        if parent_qt_instance.auto_save_thread is not None:
            parent_qt_instance.auto_save_thread.file = parent_qt_instance.current_file

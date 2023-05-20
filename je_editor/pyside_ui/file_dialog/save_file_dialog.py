import os

from PySide6.QtWidgets import QFileDialog

from je_editor.utils.file.save.save_file import write_file
from je_editor.pyside_ui.auto_save.auto_save_thread import SaveThread


def choose_file_get_save_filename(parent_qt_instance) -> None:
    """
    :param parent_qt_instance: Pyside parent
    :return: save code edit content to file
    """
    filename = QFileDialog().getSaveFileName(
        parent=parent_qt_instance,
        dir=os.getcwd()
    )[0]
    if filename is not None and filename != "":
        parent_qt_instance.current_file = filename
        write_file(filename, parent_qt_instance.code_edit.toPlainText())
        if parent_qt_instance.auto_save_thread is None:
            parent_qt_instance.auto_save_thread = SaveThread(
                parent_qt_instance.current_file,
                parent_qt_instance.code_edit.toPlainText()
            )
            parent_qt_instance.auto_save_thread.start()
        elif parent_qt_instance.auto_save_thread is not None:
            parent_qt_instance.auto_save_thread.file = parent_qt_instance.current_file

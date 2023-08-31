from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.save.save_file import write_file
from je_editor.pyside_ui.code.auto_save.auto_save_thread import SaveThread


def choose_file_get_save_file_path(parent_qt_instance: EditorMain) -> bool:
    """
    :param parent_qt_instance: Pyside parent
    :return: save code edit content to file
    """
    widget = parent_qt_instance.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        file_path = QFileDialog().getSaveFileName(
            parent=parent_qt_instance,
            dir=os.getcwd()
        )[0]
        if file_path is not None and file_path != "":
            widget.current_file = file_path
            write_file(file_path, widget.code_edit.toPlainText())
            if parent_qt_instance.auto_save_thread is None:
                widget.auto_save_thread = SaveThread(
                    widget.current_file,
                    widget.code_edit.toPlainText()
                )
                widget.auto_save_thread.start()
            elif widget.auto_save_thread is not None:
                widget.auto_save_thread.file = widget.current_file
            return True
        return False

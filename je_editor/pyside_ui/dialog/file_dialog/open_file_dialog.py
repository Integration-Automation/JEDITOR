from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
import os

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.code.auto_save.auto_save_thread import SaveThread
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_file_path(parent_qt_instance: EditorMain) -> None:
    """
    Open file and set code edit content
    :param parent_qt_instance: Pyside parent
    :return: None
    """
    widget = parent_qt_instance.tab_widget.currentWidget()
    if type(widget) is EditorWidget:
        file_path = QFileDialog().getOpenFileName(
            parent=parent_qt_instance,
            dir=os.getcwd()
        )[0]
        if file_path is not None and file_path != "":
            widget.current_file = file_path
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(
                file_content
            )
            if widget.auto_save_thread is None:
                widget.auto_save_thread = SaveThread(
                    widget.current_file,
                    widget.code_edit.toPlainText()
                )
                widget.auto_save_thread.start()
            if widget.auto_save_thread is not None:
                widget.auto_save_thread.file = widget.current_file

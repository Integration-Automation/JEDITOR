from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save.auto_save_manager import file_is_open_manager_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.save.save_file import write_file


def choose_file_get_save_file_path(parent_qt_instance: EditorMain) -> bool:
    """
    :param parent_qt_instance: Pyside parent
    :return: save code edit content to file
    """
    jeditor_logger.info(f"save_file_dialog.py choose_file_get_save_file_path"
                        f" parent_qt_instance: {parent_qt_instance}")
    widget = parent_qt_instance.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        file_path = QFileDialog().getSaveFileName(
            parent=parent_qt_instance,
            dir=os.getcwd(),
            filter="""Python file (*.py);;
            HTML file (*.html);;
            File (*.*)"""
        )[0]
        if file_path is not None and file_path != "":
            widget.current_file = file_path
            write_file(file_path, widget.code_edit.toPlainText())
            path = Path(file_path)
            file_is_open_manager_dict.update({str(path): str(path.name)})
            if widget.code_save_thread is not None:
                widget.code_save_thread.file = file_path
                widget.code_save_thread.editor = widget.code_edit
            widget.rename_self_tab()
            return True
        return False

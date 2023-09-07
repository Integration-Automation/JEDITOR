from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save import auto_save_thread
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

from PySide6.QtWidgets import QFileDialog

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.utils.file.open.open_file import read_file


def choose_file_get_open_file_path(parent_qt_instance: EditorMain) -> None:
    """
    Open file and set code edit content
    :param parent_qt_instance: Pyside parent
    :return: None
    """
    widget = parent_qt_instance.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        file_path = QFileDialog().getOpenFileName(
            parent=parent_qt_instance,
            dir=str(Path.cwd())
        )[0]
        if file_path is not None and file_path != "":
            widget.current_file = file_path
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(
                file_content
            )
            auto_save_thread.auto_save_instance.file = widget.current_file
            auto_save_thread.auto_save_instance.editor = widget.code_edit
            if not auto_save_thread.auto_save_instance.is_alive():
                auto_save_thread.auto_save_instance.start()
            user_setting_dict.update({"last_file": str(widget.current_file)})

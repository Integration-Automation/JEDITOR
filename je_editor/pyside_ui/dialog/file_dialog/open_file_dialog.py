from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from je_editor.pyside_ui.code.auto_save.auto_save_manager import init_new_auto_save_thread, file_is_open_manager_dict
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
            if file_is_open_manager_dict.get(str(Path(file_path)), None) is not None:
                widget.tab_manager.setCurrentWidget(
                    widget.tab_manager.findChild(EditorWidget, str(Path(file_path).name)))
                return
            else:
                file_is_open_manager_dict.update({file_path: str(Path(file_path).name)})
            widget.current_file = file_path
            file_content = read_file(file_path)[1]
            widget.code_edit.setPlainText(
                file_content
            )
            if widget.current_file is not None and widget.code_save_thread is None:
                init_new_auto_save_thread(widget.current_file, widget)
            else:
                widget.code_save_thread.file = widget.current_file
            user_setting_dict.update({"last_file": str(widget.current_file)})
            widget.rename_self_tab()

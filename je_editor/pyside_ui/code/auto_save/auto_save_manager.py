from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorWidget

from je_editor.pyside_ui.code.auto_save.auto_save_thread import CodeEditSaveThread

auto_save_manager_dict = {

}


def init_new_auto_save_thread(file_path: str, widget: EditorWidget):
    widget.current_file = file_path
    if auto_save_manager_dict.get(file_path, None) is None:
        widget.code_save_thread = CodeEditSaveThread(
            file_to_save=widget.current_file, editor=widget.code_edit)
        auto_save_manager_dict.update({
            file_path: widget.code_save_thread
        })
        widget.code_save_thread.start()

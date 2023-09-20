from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMessageBox

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def please_close_current_running_messagebox(ui_we_want_to_set: EditorMain):
    please_stop_current_running_program_messagebox = QMessageBox(ui_we_want_to_set)
    please_stop_current_running_program_messagebox.setText(
        language_wrapper.language_word_dict.get("please_stop_current_running_program")
    )
    please_stop_current_running_program_messagebox.show()

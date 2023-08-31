from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def set_ui(ui_we_want_to_set: EditorMain):
    # set qt window
    ui_we_want_to_set.setWindowTitle("JEditor")

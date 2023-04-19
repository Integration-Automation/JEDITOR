import sys

from PySide6.QtWidgets import QApplication

from je_editor.tkinter_ui.editor_main_ui.tkinter_editor import EditorMain as TkinterEditor
from je_editor.pyside_ui.editor_main_ui.main_editor import EditorMain as PysideEditor


def start_editor(editor: str = "tkinter", use_theme=None, **kwargs):
    if editor == "pyside":
        new_editor = QApplication(sys.argv)
        window = PysideEditor()
        window.show()
        sys.exit(new_editor.exec_())
    else:
        new_editor = TkinterEditor(use_theme=use_theme, **kwargs)
        new_editor.start_editor()
    return new_editor

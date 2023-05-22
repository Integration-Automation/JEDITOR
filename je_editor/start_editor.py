import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor.pyside_ui.main_ui.editor_main_ui.main_editor import EditorMain


def start_editor(debug_mode: bool = False, **kwargs) -> None:
    new_editor = QApplication(sys.argv)
    window = EditorMain(debug_mode, **kwargs)
    apply_stylesheet(new_editor, theme='dark_amber.xml')
    window.showMaximized()
    try:
        window.startup_setting()
    except Exception as error:
        print(repr(error))
    sys.exit(new_editor.exec())

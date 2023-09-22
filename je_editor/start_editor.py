import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor.pyside_ui.main_ui.main_editor import EditorMain


def start_editor(debug_mode: bool = False, ) -> None:
    new_editor = QCoreApplication.instance()
    if new_editor is None:
        new_editor = QApplication(sys.argv)
    window = EditorMain(debug_mode)
    apply_stylesheet(new_editor, theme='dark_amber.xml')
    window.showMaximized()
    sys.exit(new_editor.exec())

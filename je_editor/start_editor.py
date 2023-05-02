import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor.pyside_ui.main_ui.editor_main_ui.main_editor import EditorMain


def start_editor(**kwargs):
    new_editor = QApplication(sys.argv)
    window = EditorMain()
    apply_stylesheet(new_editor, theme='dark_amber.xml')
    window.showMaximized()
    window.startup_setting()
    sys.exit(new_editor.exec())

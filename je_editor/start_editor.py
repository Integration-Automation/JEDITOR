import sys

from PySide6.QtWidgets import QApplication

from je_editor.pyside_ui.main_ui.editor_main_ui.main_editor import EditorMain


def start_editor(**kwargs):
    new_editor = QApplication(sys.argv)
    window = EditorMain()
    window.show()
    sys.exit(new_editor.exec_())

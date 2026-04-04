"""
CI smoke test: start JEditor with an extend tab, verify it opens and closes cleanly.
"""
import sys
import os

from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor import EDITOR_EXTEND_TAB
from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from je_editor.plugins.plugin_loader import load_external_plugins


class TestUI(QWidget):

    def __init__(self):
        super().__init__()
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("")
        self.line_edit = QLineEdit()
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.show_input_text)
        self.grid_layout.addWidget(self.label, 0, 0)
        self.grid_layout.addWidget(self.line_edit, 1, 0)
        self.grid_layout.addWidget(self.submit_button, 2, 0)

    def show_input_text(self):
        self.label.setText(self.line_edit.text())


if __name__ == "__main__":
    EDITOR_EXTEND_TAB.update({"test": TestUI})

    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    load_external_plugins()
    window = EditorMain(debug_mode=True)
    apply_stylesheet(app, theme="dark_amber.xml")
    window.showMaximized()

    # debug_mode=True 會自動在 10 秒後呼叫 QApplication.quit()
    # debug_mode=True auto-calls QApplication.quit() after 10 seconds
    ret = app.exec()
    sys.exit(ret)

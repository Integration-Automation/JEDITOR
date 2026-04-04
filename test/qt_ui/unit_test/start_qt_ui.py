"""
CI smoke test: start JEditor in debug mode, verify it opens and closes cleanly.
"""
import sys
import os

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from je_editor.pyside_ui.main_ui.main_editor import EditorMain
from je_editor.plugins.plugin_loader import load_external_plugins

if __name__ == "__main__":
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

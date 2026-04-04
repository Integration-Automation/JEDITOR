"""
CI smoke test: start JEditor with an extend tab, verify it opens and closes cleanly.
"""
import sys
import os

# Force offscreen rendering for CI (must be set before any Qt import)
if "CI" in os.environ or os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def _log(msg):
    """Write directly to original stderr, bypassing any redirection."""
    sys.__stderr__.write(f"[CI-TEST] {msg}\n")
    sys.__stderr__.flush()


from PySide6.QtWidgets import QWidget, QGridLayout, QLineEdit, QPushButton, QLabel


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
    try:
        _log("Step 1: Importing...")
        from PySide6.QtCore import QCoreApplication, QTimer
        from PySide6.QtWidgets import QApplication
        from qt_material import apply_stylesheet

        from je_editor import EDITOR_EXTEND_TAB
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        from je_editor.plugins.plugin_loader import load_external_plugins

        EDITOR_EXTEND_TAB.update({"test": TestUI})

        _log("Step 2: Creating QApplication...")
        app = QCoreApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        _log("Step 3: Loading plugins...")
        load_external_plugins()

        _log("Step 4: Creating EditorMain(debug_mode=True)...")
        window = EditorMain(debug_mode=True)

        _log("Step 5: Applying stylesheet...")
        apply_stylesheet(app, theme="dark_amber.xml")
        window.showMaximized()

        _log("Step 6: Entering event loop (quit in ~10s)...")
        app.exec()

        _log("Step 7: Event loop ended, exiting...")
        os._exit(0)

    except SystemExit as e:
        _log(f"SystemExit caught: code={e.code}")
        os._exit(e.code if isinstance(e.code, int) else 0)
    except Exception as e:
        _log(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc(file=sys.__stderr__)
        os._exit(1)

"""
CI smoke test: start JEditor in debug mode, verify it opens and closes cleanly.
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


if __name__ == "__main__":
    try:
        _log("Step 1: Importing Qt...")
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtWidgets import QApplication
        from qt_material import apply_stylesheet

        _log("Step 2: Importing JEditor...")
        from je_editor.pyside_ui.main_ui.main_editor import EditorMain
        from je_editor.plugins.plugin_loader import load_external_plugins

        _log("Step 3: Creating QApplication...")
        app = QCoreApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        _log("Step 4: Loading plugins...")
        load_external_plugins()

        _log("Step 5: Creating EditorMain(debug_mode=True)...")
        window = EditorMain(debug_mode=True)

        _log("Step 6: Applying stylesheet...")
        apply_stylesheet(app, theme="dark_amber.xml")
        window.showMaximized()

        _log("Step 7: Entering event loop (quit in ~10s)...")
        app.exec()

        _log("Step 8: Event loop ended, exiting...")
        os._exit(0)

    except SystemExit as e:
        _log(f"SystemExit caught: code={e.code}")
        raise
    except Exception as e:
        _log(f"Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc(file=sys.__stderr__)
        os._exit(1)

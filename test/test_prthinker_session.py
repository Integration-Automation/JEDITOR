"""Review preparation stays off the GUI thread and forwards terminal events."""

import threading
from types import SimpleNamespace

from PySide6.QtWidgets import QMainWindow
from shiboken6 import delete

from je_editor.core.diagnostics.diagnostic_model import DiagnosticStore
from je_editor.pyside_ui.review import prthinker_actions as actions
from je_editor.pyside_ui.review.prthinker_session import PRThinkerSession


def test_session_forwards_terminal_and_progress(qtbot, tmp_path):
    window = QMainWindow()
    qtbot.addWidget(window)
    session = PRThinkerSession(DiagnosticStore(), tmp_path, window)
    session.diagnostics.begin("review")
    with qtbot.waitSignal(session.terminal):
        session.receive({"protocol_version": 1, "request_id": "review",
                         "event": "terminal", "status": "completed"})
    assert session.diagnostics.status == "completed"
    assert window.statusBar().currentMessage() == "prthinker: completed"
    session.deleteLater()


def test_saved_diff_preparation_runs_in_background(qtbot, monkeypatch, tmp_path):
    window = QMainWindow()
    qtbot.addWidget(window)
    window.services = SimpleNamespace(diagnostics=DiagnosticStore())
    window.tab_widget = SimpleNamespace(currentWidget=lambda: SimpleNamespace(current_file=str(tmp_path / "mod.py")))
    ready = threading.Event()
    threads, reviews = [], []

    def prepare(path):
        threads.append(threading.get_ident())
        ready.wait(2)
        return path.parent, "diff"

    class Session:
        def __init__(self, *_args):
            pass

        def start(self, *_args, **_kwargs):
            pass

        def review(self, diff):
            reviews.append(diff)

    monkeypatch.setattr(actions, "saved_file_diff", prepare)
    monkeypatch.setattr(actions, "PRThinkerSession", Session)
    assert actions.review_current_file(window)
    assert not reviews
    ready.set()
    qtbot.waitUntil(lambda: reviews == ["diff"])
    assert threads[0] != threading.get_ident()


def test_late_terminal_after_window_destruction_is_safe(qtbot, tmp_path):
    window = QMainWindow()
    session = PRThinkerSession(DiagnosticStore(), tmp_path, window)
    session.diagnostics.begin("late")
    delete(window)
    with qtbot.waitSignal(session.terminal):
        session.receive({"protocol_version": 1, "request_id": "late",
                         "event": "terminal", "status": "cancelled"})
    session.deleteLater()

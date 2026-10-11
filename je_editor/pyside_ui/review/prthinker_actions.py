"""Review actions shared by both editor shells / 兩個編輯器共用的審查動作。"""

import difflib
import subprocess
import sys
from pathlib import Path
from threading import Thread

from PySide6.QtCore import QObject, Signal, Slot

from je_editor.pyside_ui.review.prthinker_session import PRThinkerSession


def saved_file_diff(file_path: Path) -> tuple[Path, str]:
    """Review changes, or the whole saved file / 審查變更或完整已存檔內容。"""
    result = subprocess.run(["git", "-C", str(file_path.parent), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, check=False, timeout=10)
    workdir = Path(result.stdout.strip()) if result.returncode == 0 else file_path.parent
    relative = file_path.resolve().relative_to(workdir.resolve()).as_posix()
    if result.returncode == 0:
        diff = subprocess.run(["git", "-C", str(workdir), "diff", "HEAD", "--", relative],
                              capture_output=True, text=True, check=False, timeout=10).stdout
        if diff.strip():
            return workdir, diff
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    return workdir, "".join(difflib.unified_diff([], lines, fromfile="a/" + relative, tofile="b/" + relative))


class ReviewPreparation(QObject):
    """Prepare saved content off the GUI thread / 在背景準備已存檔內容。"""

    prepared = Signal(object, str)
    failed = Signal(str)

    def __init__(self, window, environment, arguments):
        super().__init__(window)
        self.window = window
        self.environment = environment
        self.arguments = arguments
        self.cancelled = False
        self.prepared.connect(self._start)
        window.destroyed.connect(self.cancel)

    @Slot()
    def cancel(self):
        self.cancelled = True

    def prepare(self, path):
        try:
            workdir, diff = saved_file_diff(path)
            if not self.cancelled:
                self.prepared.emit(workdir, diff)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            if not self.cancelled:
                self.failed.emit(str(error))

    @Slot(object, str)
    def _start(self, workdir, diff):
        if self.cancelled:
            return
        session = PRThinkerSession(self.window.services.diagnostics, workdir, self.window)
        self.window.prthinker_session = session
        session.start(str(getattr(self.window, "python_compiler", None) or sys.executable),
                      arguments=self.arguments, environment=self.environment)
        session.review(diff)


def review_current_file(window, *, environment=None, arguments=()):
    """Start the same isolated protocol session / 啟動相同的隔離協定工作階段。"""
    widget = window.tab_widget.currentWidget()
    path = getattr(widget, "current_file", "")
    if not path:
        return False
    previous = getattr(window, "prthinker_session", None)
    if previous:
        previous.close()
    previous_preparation = getattr(window, "prthinker_preparation", None)
    if previous_preparation:
        previous_preparation.cancel()
    preparation = ReviewPreparation(window, environment, arguments)
    window.prthinker_preparation = preparation
    Thread(target=preparation.prepare, args=(Path(path),), daemon=True).start()
    return True


def cancel_review(window):
    """Request graceful cancellation / 請求正常取消。"""
    preparation = getattr(window, "prthinker_preparation", None)
    if preparation:
        preparation.cancel()
    session = getattr(window, "prthinker_session", None)
    if session:
        session.cancel()

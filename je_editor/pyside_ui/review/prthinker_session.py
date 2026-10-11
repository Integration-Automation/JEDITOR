"""Qt subprocess lifecycle for review / 審查的 Qt 子行程生命週期。"""

import json
import uuid
import weakref
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal, QCoreApplication, QTimer
from shiboken6 import isValid

from je_editor.adapters.review.prthinker_diagnostics import ReviewDiagnostics


class PRThinkerSession(QObject):
    """Protocol I/O stays on the GUI thread / 協定輸入輸出留在 GUI 執行緒。"""

    progress = Signal(dict)
    terminal = Signal(dict)
    proposal = Signal(dict)
    failure = Signal(str)

    def __init__(self, diagnostics, workdir: Path, parent=None):
        app = QCoreApplication.instance()
        super().__init__(app or parent)
        self.window = weakref.ref(parent) if parent else lambda: None
        if parent:
            parent.destroyed.connect(self.close)
        self.diagnostics = ReviewDiagnostics(diagnostics, workdir)
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(workdir))
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.readyReadStandardError.connect(self._read_error)
        self.process.errorOccurred.connect(self._process_error)
        self.process.finished.connect(self._process_finished)
        self.buffer = b""
        self.pending = []
        self.process.started.connect(self._flush_pending)
        self.progress.connect(self._show_status)
        self.terminal.connect(self._show_status)
        if app:
            app.aboutToQuit.connect(self.process.kill)

    def _show_status(self, event):
        window = self.window()
        if window and isValid(window) and hasattr(window, "statusBar"):
            window.statusBar().showMessage("prthinker: " + str(event.get("stage", event.get("status", ""))))

    def _process_error(self, _error):
        self.failure.emit(self.process.errorString())
        self._process_finished(-1, None)

    def _process_finished(self, code, _status):
        if self.diagnostics.request_id and self.diagnostics.status not in ("completed", "cancelled", "failed"):
            self.receive({"protocol_version": 1, "request_id": self.diagnostics.request_id,
                          "event": "terminal", "status": "failed", "exit_code": code})

    def start(self, interpreter: str, arguments=(), environment=None):
        env = QProcessEnvironment.systemEnvironment()
        for name, value in (environment or {}).items():
            env.insert(name, value)
        self.process.setProcessEnvironment(env)
        self.process.start(interpreter, ["-m", "prthinker", "ide", *arguments])

    def review(self, diff: str):
        request_id = uuid.uuid4().hex
        self.diagnostics.begin(request_id)
        self.send({"protocol_version": 1, "request_id": request_id, "operation": "review",
                   "diff": diff, "workdir": str(self.diagnostics.workdir)})
        return request_id

    def cancel(self):
        self.send({"protocol_version": 1, "request_id": uuid.uuid4().hex, "operation": "cancel",
                   "target_request_id": self.diagnostics.request_id})

    def send(self, message: dict):
        encoded = (json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8")
        if self.process.state() != QProcess.ProcessState.Running:
            self.pending.append(encoded)
        else:
            self.process.write(encoded)

    def _flush_pending(self):
        for message in self.pending:
            self.process.write(message)
        self.pending.clear()

    def _read_output(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\n", 1)
            try:
                self.receive(json.loads(raw))
            except (ValueError, KeyError, TypeError) as error:
                self.failure.emit(str(error))

    def receive(self, event: dict):
        if self.diagnostics.receive(event):
            kind = event.get("event")
            if kind == "progress":
                self.progress.emit(event)
            elif kind == "terminal":
                self.terminal.emit(event)
            elif kind == "patch_proposal":
                self.proposal.emit(event)

    def _read_error(self):
        # Logs may contain provider messages; do not mirror credentials to UI.
        # 記錄可能含供應者訊息，不將憑證複製到介面。
        self.process.readAllStandardError()

    def close(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.cancel()
            self.process.closeWriteChannel()
            QTimer.singleShot(5000, self.process.kill)

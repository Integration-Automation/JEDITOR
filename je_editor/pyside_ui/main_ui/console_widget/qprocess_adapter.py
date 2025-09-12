import os

from PySide6.QtCore import QObject, QProcess, Signal, QTimer


class ConsoleProcessAdapter(QObject):
    started = Signal()
    finished = Signal(int, QProcess.ExitStatus)
    stdout = Signal(str)
    stderr = Signal(str)
    system = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.started.connect(self.started)
        self.proc.finished.connect(self.finished)

    def set_cwd(self, path: str):
        self.proc.setWorkingDirectory(path)

    def start_shell(self, shell: str = "auto"):
        if self.is_running():
            self.system.emit("Shell already running")
            return
        program, args = self._build_shell_command(shell)
        self.proc.start(program, args)

        if os.name == "nt":
            QTimer.singleShot(500, lambda: self.send_command("chcp 65001"))

    def send_command(self, cmd: str):
        if not self.is_running():
            self.system.emit("Shell not running")
            return
        self.proc.write((cmd + "\n").encode("utf-8"))

    def stop(self):
        if not self.is_running():
            return
        self.proc.terminate()
        QTimer.singleShot(1000, lambda: self.is_running() and self.proc.kill())

    def is_running(self):
        return self.proc.state() != QProcess.ProcessState.NotRunning

    def _on_stdout(self):
        self.stdout.emit(bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace"))

    def _on_stderr(self):
        self.stderr.emit(bytes(self.proc.readAllStandardError()).decode("utf-8", errors="replace"))

    def _build_shell_command(self, shell: str):
        if shell == "auto":
            shell = "cmd" if os.name == "nt" else "bash"
        if os.name == "nt":
            if shell == "powershell":
                return "powershell.exe", ["-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass"]
            return "cmd.exe", []
        return ("/bin/bash" if shell == "bash" else "/bin/sh"), []

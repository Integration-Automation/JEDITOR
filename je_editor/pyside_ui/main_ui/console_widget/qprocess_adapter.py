import os

from PySide6.QtCore import QObject, QProcess, Signal, QTimer


class ConsoleProcessAdapter(QObject):
    """
    ConsoleProcessAdapter 負責管理 QProcess，提供互動式 shell 的啟動、指令傳送與輸出監聽。
    ConsoleProcessAdapter manages QProcess, providing interactive shell start, command sending, and output handling.
    """

    # 定義訊號 / Define signals
    started = Signal()  # 當子程序啟動時發射 / Emitted when process starts
    finished = Signal(int, QProcess.ExitStatus)  # 當子程序結束時發射 / Emitted when process finishes
    stdout = Signal(str)  # 標準輸出訊號 / Standard output signal
    stderr = Signal(str)  # 錯誤輸出訊號 / Standard error signal
    system = Signal(str)  # 系統訊息訊號 / System message signal

    def __init__(self, parent=None):
        super().__init__(parent)
        # 建立 QProcess 物件 / Create QProcess object
        self.proc = QProcess(self)
        # 設定輸出通道分離 (stdout / stderr) / Separate stdout and stderr
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels)

        # 綁定事件處理函式 / Connect signals to handlers
        self.proc.readyReadStandardOutput.connect(self._on_stdout)
        self.proc.readyReadStandardError.connect(self._on_stderr)
        self.proc.started.connect(self.started)
        self.proc.finished.connect(self.finished)

    # 設定工作目錄 / Set working directory
    def set_cwd(self, path: str):
        self.proc.setWorkingDirectory(path)

    # 啟動 shell / Start shell
    def start_shell(self, shell: str = "auto"):
        if self.is_running():
            self.system.emit("Shell already running")  # 如果已經在執行，發送提示 / Emit message if already running
            return
        program, args = self._build_shell_command(shell)  # 建立 shell 指令 / Build shell command
        self.proc.start(program, args)  # 啟動子程序 / Start process

        # Windows 特殊處理：設定 UTF-8 編碼 / Windows-specific: set UTF-8 encoding
        if os.name == "nt":
            QTimer.singleShot(500, lambda: self.send_command("chcp 65001"))

    # 傳送指令到 shell / Send command to shell
    def send_command(self, cmd: str):
        if not self.is_running():
            self.system.emit("Shell not running")  # 如果 shell 未啟動，發送提示 / Emit message if not running
            return
        self.proc.write((cmd + "\n").encode("utf-8"))  # 傳送指令並換行 / Send command with newline

    # 停止 shell / Stop shell
    def stop(self):
        if not self.is_running():
            return
        self.proc.terminate()  # 嘗試正常結束 / Try graceful termination
        # 如果 1 秒後仍在執行，強制 kill / Force kill if still running after 1s
        QTimer.singleShot(1000, lambda: self.is_running() and self.proc.kill())

    # 判斷是否正在執行 / Check if process is running
    def is_running(self):
        return self.proc.state() != QProcess.ProcessState.NotRunning

    # 處理標準輸出 / Handle standard output
    def _on_stdout(self):
        self.stdout.emit(bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace"))

    # 處理錯誤輸出 / Handle standard error
    def _on_stderr(self):
        self.stderr.emit(bytes(self.proc.readAllStandardError()).decode("utf-8", errors="replace"))

    # 建立 shell 指令 / Build shell command
    def _build_shell_command(self, shell: str):
        if shell == "auto":
            shell = "cmd" if os.name == "nt" else "bash"  # Windows 預設 cmd，Linux/macOS 預設 bash
        if os.name == "nt":
            if shell == "powershell":
                return "powershell.exe", ["-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass"]
            return "cmd.exe", []
        # Linux/macOS 預設 bash，否則使用 sh / Default bash, fallback to sh
        return ("/bin/bash" if shell == "bash" else "/bin/sh"), []
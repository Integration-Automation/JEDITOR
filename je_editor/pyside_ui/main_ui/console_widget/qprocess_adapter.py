import os

from PySide6.QtCore import QObject, QProcess, Signal, QTimer

# Windows 啟動 shell 後切換 UTF-8 code page 的延遲 / Delay before switching to UTF-8 on Windows
UTF8_CODEPAGE_DELAY_MS = 500
# terminate 之後改用 kill 的等待時間 / How long to wait after terminate before killing
KILL_DELAY_MS = 1000


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

    def __init__(self, parent: QObject | None = None) -> None:
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
    def set_cwd(self, path: str) -> None:
        self.proc.setWorkingDirectory(path)

    # 啟動 shell / Start shell
    def start_shell(self, shell: str = "auto") -> None:
        if self.is_running():
            self.system.emit("Shell already running")  # 如果已經在執行，發送提示 / Emit message if already running
            return
        program, args = self._build_shell_command(shell)  # 建立 shell 指令 / Build shell command
        self.proc.start(program, args)  # 啟動子程序 / Start process

        # Windows 特殊處理：設定 UTF-8 編碼 / Windows-specific: set UTF-8 encoding
        # 以 self 當作 context 物件，這個介面卡被銷毀時 Qt 會自動丟棄尚未觸發的呼叫；
        # 沒有 context 的 singleShot 會在物件死後才觸發，存取到已刪除的 QProcess。
        # Passing self as the context object lets Qt drop the pending call when this
        # adapter dies; a context-less singleShot fires after death and touches a
        # already-deleted QProcess.
        if os.name == "nt":
            QTimer.singleShot(UTF8_CODEPAGE_DELAY_MS, self, self._enable_utf8_codepage)

    # 切換到 UTF-8 code page / Switch the shell to the UTF-8 code page
    def _enable_utf8_codepage(self) -> None:
        if self.is_running():
            self.send_command("chcp 65001")

    # 傳送指令到 shell / Send command to shell
    def send_command(self, cmd: str) -> None:
        if not self.is_running():
            self.system.emit("Shell not running")  # 如果 shell 未啟動，發送提示 / Emit message if not running
            return
        self.proc.write((cmd + "\n").encode("utf-8"))  # 傳送指令並換行 / Send command with newline

    # 停止 shell / Stop shell
    def stop(self) -> None:
        if not self.is_running():
            return
        self.proc.terminate()  # 嘗試正常結束 / Try graceful termination
        # 如果 1 秒後仍在執行，強制 kill / Force kill if still running after 1s
        QTimer.singleShot(KILL_DELAY_MS, self, self._kill_if_still_running)

    # 強制結束仍在執行的 shell / Force kill a shell that ignored terminate
    def _kill_if_still_running(self) -> None:
        if self.is_running():
            self.proc.kill()

    def shutdown(self, wait_ms: int = KILL_DELAY_MS) -> None:
        """
        同步關閉 shell，確保 QProcess 不會在子程序仍執行時被銷毀
        Shut the shell down synchronously so the QProcess is never destroyed
        while its child process is still running.

        :param wait_ms: 每個階段的等待毫秒數 / Milliseconds waited at each stage
        """
        if not self.is_running():
            return
        self.proc.terminate()
        if self.proc.waitForFinished(wait_ms):
            return
        self.proc.kill()
        self.proc.waitForFinished(wait_ms)

    # 判斷是否正在執行 / Check if process is running
    def is_running(self) -> bool:
        return self.proc.state() != QProcess.ProcessState.NotRunning

    # 處理標準輸出 / Handle standard output
    def _on_stdout(self) -> None:
        self.stdout.emit(bytes(self.proc.readAllStandardOutput()).decode("utf-8", errors="replace"))

    # 處理錯誤輸出 / Handle standard error
    def _on_stderr(self) -> None:
        self.stderr.emit(bytes(self.proc.readAllStandardError()).decode("utf-8", errors="replace"))

    # 建立 shell 指令 / Build shell command
    def _build_shell_command(self, shell: str) -> tuple[str, list[str]]:
        if shell == "auto":
            shell = "cmd" if os.name == "nt" else "bash"  # Windows 預設 cmd，Linux/macOS 預設 bash
        if os.name == "nt":
            if shell == "powershell":
                return "powershell.exe", ["-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass"]
            return "cmd.exe", []
        # Linux/macOS 預設 bash，否則使用 sh / Default bash, fallback to sh
        return ("/bin/bash" if shell == "bash" else "/bin/sh"), []

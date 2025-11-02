import os

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QTextCursor, QColor, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLineEdit,
    QPushButton, QLabel, QFileDialog, QComboBox
)

from je_editor.pyside_ui.main_ui.console_widget.qprocess_adapter import ConsoleProcessAdapter
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class ConsoleWidget(QWidget):
    """
    ConsoleWidget 提供一個互動式終端機介面，讓使用者可以輸入指令並查看輸出。
    ConsoleWidget provides an interactive console interface for running commands and viewing output.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_word_dict_get = language_wrapper.language_word_dict.get

        # 初始化子程序控制器 / Initialize process adapter
        self.proc = ConsoleProcessAdapter(self)
        self.proc.stdout.connect(self.append_text)  # 標準輸出 / Standard output
        self.proc.stderr.connect(lambda t: self.append_text(t, "#d33"))  # 錯誤輸出 (紅色) / Error output (red)
        self.proc.system.connect(
            lambda t: self.append_text(f"{self.language_word_dict_get('dynamic_console_system_prefix')}{t}\n", "#888")
        )
        self.proc.started.connect(lambda: self.proc.system.emit(self.language_word_dict_get("dynamic_console_running")))
        self.proc.finished.connect(self.on_finished)

        # 指令歷史紀錄 / Command history
        self.history, self.history_index = [], -1

        # 輸出區域 / Output area
        self.output = QPlainTextEdit(readOnly=True)
        self.output.setMaximumBlockCount(10000)  # 最多保留 10000 行 / Keep up to 10000 lines
        self.output.setStyleSheet("font-family: Consolas, monospace;")

        # 輸入框 / Input field
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command")  # 預設提示文字 / Placeholder text
        self.input.returnPressed.connect(self.run_command)  # 按 Enter 執行指令 / Run command on Enter
        self.input.installEventFilter(self)  # 安裝事件過濾器，用於上下鍵瀏覽歷史 / Install event filter for history navigation

        # 控制按鈕 / Control buttons
        self.btn_run = QPushButton(self.language_word_dict_get("dynamic_console_run"))
        self.btn_run.clicked.connect(self.run_command)

        self.btn_stop = QPushButton(self.language_word_dict_get("dynamic_console_stop"))
        self.btn_stop.clicked.connect(self.proc.stop)

        self.btn_clear = QPushButton(self.language_word_dict_get("dynamic_console_clear"))
        self.btn_clear.clicked.connect(self.output.clear)

        # 工作目錄顯示與選擇 / Current working directory display and picker
        self.cwd_label = QLabel(f"{self.language_word_dict_get('dynamic_console_cwd')}: {os.getcwd()}")
        self.btn_pick_cwd = QPushButton("…")
        self.btn_pick_cwd.clicked.connect(self.pick_cwd)

        # Shell 選擇下拉選單 / Shell selection combobox
        self.shell_combo = QComboBox()
        self.shell_combo.addItems(["auto", "cmd", "powershell", "bash", "sh"])

        # 版面配置：上方 (工作目錄 + Shell 選擇) / Layout: Top (CWD + Shell selection)
        top = QHBoxLayout()
        top.addWidget(self.cwd_label)
        top.addWidget(self.btn_pick_cwd)
        top.addStretch()
        top.addWidget(QLabel(self.language_word_dict_get("dynamic_console_shell")))
        top.addWidget(self.shell_combo)

        # 版面配置：中間 (輸入框 + 按鈕) / Layout: Middle (Input + Buttons)
        mid = QHBoxLayout()
        mid.addWidget(self.input, 1)
        mid.addWidget(self.btn_run)
        mid.addWidget(self.btn_stop)
        mid.addWidget(self.btn_clear)

        # 主版面配置 / Main layout
        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.output, 1)
        lay.addLayout(mid)

        # 初始化狀態訊息 / Initial status message
        self.proc.system.emit(self.language_word_dict_get("dynamic_console_ready"))

        # 啟動互動式 shell / Start interactive shell
        self.proc.start_shell(self.shell_combo.currentText())

    # 事件過濾器：支援上下鍵瀏覽歷史指令
    # Event filter: Support navigating command history with Up/Down keys
    def eventFilter(self, obj, event):
        if obj is self.input and isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self.history_prev()
                return True
            if event.key() == Qt.Key.Key_Down:
                self.history_next()
                return True
        return super().eventFilter(obj, event)

    # 瀏覽上一個歷史指令 / Navigate to previous command in history
    def history_prev(self):
        if not self.history: return
        self.history_index = len(self.history) - 1 if self.history_index < 0 else max(0, self.history_index - 1)
        self.input.setText(self.history[self.history_index])
        self.input.end(False)

    # 瀏覽下一個歷史指令 / Navigate to next command in history
    def history_next(self):
        if not self.history: return
        if self.history_index < 0: return
        self.history_index += 1
        if self.history_index >= len(self.history):
            self.history_index = -1
            self.input.clear()
        else:
            self.input.setText(self.history[self.history_index])
            self.input.end(False)

    # 選擇新的工作目錄 / Pick a new working directory
    def pick_cwd(self):
        d = QFileDialog.getExistingDirectory(self, "Select working directory", os.getcwd())
        if d:
            self.proc.set_cwd(d)
            self.cwd_label.setText(f"{self.language_word_dict_get('dynamic_console_cwd')}: {d}")
            self.proc.system.emit(f'cd "{d}"')

    # 在輸出區域新增文字 (支援顏色) / Append text to output area (with optional color)
    def append_text(self, text, color=None):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = self.output.currentCharFormat()
        if color:
            fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    # 執行輸入的指令 / Run the entered command
    def run_command(self):
        cmd = self.input.text().strip()
        if not cmd: return
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.history_index = -1
        self.append_text(f"{self.language_word_dict_get('dynamic_console_prompt')}{cmd}\n", "#0aa")
        self.proc.send_command(cmd)
        self.input.clear()

    # 子程序結束時的處理 / Handle process finished event
    def on_finished(self, code, status):
        self.append_text(
            f"\n{self.language_word_dict_get('dynamic_console_done').format(code=code, status=status)}\n",
            "#888"
        )
        self.proc.system.emit(self.language_word_dict_get("dynamic_console_ready"))

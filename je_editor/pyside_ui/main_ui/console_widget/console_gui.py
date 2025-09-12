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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.language_word_dict_get = language_wrapper.language_word_dict.get
        self.proc = ConsoleProcessAdapter(self)
        self.proc.stdout.connect(self.append_text)
        self.proc.stderr.connect(lambda t: self.append_text(t, "#d33"))
        self.proc.system.connect(
            lambda t: self.append_text(f"{self.language_word_dict_get('dynamic_console_system_prefix')}{t}\n", "#888"))
        self.proc.started.connect(lambda: self.proc.system.emit(self.language_word_dict_get("dynamic_console_running")))
        self.proc.finished.connect(self.on_finished)

        self.history, self.history_index = [], -1

        self.output = QPlainTextEdit(readOnly=True)
        self.output.setMaximumBlockCount(10000)
        self.output.setStyleSheet("font-family: Consolas, monospace;")

        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter command")
        self.input.returnPressed.connect(self.run_command)
        self.input.installEventFilter(self)

        self.btn_run = QPushButton(self.language_word_dict_get("dynamic_console_run"))
        self.btn_run.clicked.connect(self.run_command)
        self.btn_stop = QPushButton(self.language_word_dict_get("dynamic_console_stop"))
        self.btn_stop.clicked.connect(self.proc.stop)
        self.btn_clear = QPushButton(self.language_word_dict_get("dynamic_console_clear"))
        self.btn_clear.clicked.connect(self.output.clear)

        self.cwd_label = QLabel(f"{self.language_word_dict_get('dynamic_console_cwd')}: {os.getcwd()}")
        self.btn_pick_cwd = QPushButton("…")
        self.btn_pick_cwd.clicked.connect(self.pick_cwd)

        self.shell_combo = QComboBox()
        self.shell_combo.addItems(["auto", "cmd", "powershell", "bash", "sh"])

        top = QHBoxLayout()
        top.addWidget(self.cwd_label)
        top.addWidget(self.btn_pick_cwd)
        top.addStretch()
        top.addWidget(QLabel(self.language_word_dict_get("dynamic_console_shell")))
        top.addWidget(self.shell_combo)

        mid = QHBoxLayout()
        mid.addWidget(self.input, 1)
        mid.addWidget(self.btn_run)
        mid.addWidget(self.btn_stop)
        mid.addWidget(self.btn_clear)

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.output, 1)
        lay.addLayout(mid)

        self.proc.system.emit(self.language_word_dict_get("dynamic_console_ready"))
        # 啟動互動式 shell
        self.proc.start_shell(self.shell_combo.currentText())

    def eventFilter(self, obj, event):
        if obj is self.input and isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self.history_prev()
                return True
            if event.key() == Qt.Key.Key_Down:
                self.history_next()
                return True
        return super().eventFilter(obj, event)

    def history_prev(self):
        if not self.history: return
        self.history_index = len(self.history) - 1 if self.history_index < 0 else max(0, self.history_index - 1)
        self.input.setText(self.history[self.history_index])
        self.input.end(False)

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

    def pick_cwd(self):
        d = QFileDialog.getExistingDirectory(self, "Select working directory", os.getcwd())
        if d:
            self.proc.set_cwd(d)
            self.cwd_label.setText(f"{self.language_word_dict_get('dynamic_console_cwd')}: {d}")
            self.proc.system.emit(f'cd "{d}"')

    def append_text(self, text, color=None):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = self.output.currentCharFormat()
        if color: fmt.setForeground(QColor(color))
        cursor.setCharFormat(fmt)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def run_command(self):
        cmd = self.input.text().strip()
        if not cmd: return
        if not self.history or self.history[-1] != cmd:
            self.history.append(cmd)
        self.history_index = -1
        self.append_text(f"{self.language_word_dict_get('dynamic_console_prompt')}{cmd}\n", "#0aa")
        self.proc.send_command(cmd)
        self.input.clear()

    def on_finished(self, code, status):
        self.append_text(f"\n{self.language_word_dict_get('dynamic_console_done').format(code=code, status=status)}\n",
                         "#888")
        self.proc.system.emit(self.language_word_dict_get("dynamic_console_ready"))

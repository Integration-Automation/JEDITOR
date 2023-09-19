from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QLineEdit, QBoxLayout, QPushButton, QHBoxLayout

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorWidget

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class DebuggerInput(QWidget):

    def __init__(self, main_window: EditorWidget):
        super().__init__()
        self.main_window = main_window
        self.main_window.code_difference_result.setCurrentWidget(self.main_window.debugger_result)
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.command_input = QLineEdit()
        self.send_command_button = QPushButton()
        self.send_command_button.setText(language_wrapper.language_word_dict.get("debugger_input_send_command"))
        self.send_command_button.clicked.connect(self.send_command)
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.send_command_button)
        self.box_layout.addWidget(self.command_input)
        self.box_layout.addLayout(self.box_h_layout)
        self.setWindowTitle(language_wrapper.language_word_dict.get("editor_debugger"))
        self.setLayout(self.box_layout)

    def send_command(self):
        if self.main_window.exec_python_debugger is not None:
            process_stdin = self.main_window.exec_python_debugger.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()


from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLineEdit, QBoxLayout, QPushButton, QHBoxLayout

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorWidget

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


class ProcessInput(QWidget):

    def __init__(self, main_window: EditorWidget, process_type: str = "debugger"):
        super().__init__()
        # Attr
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # UI setting
        self.main_window = main_window
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.command_input = QLineEdit()
        self.send_command_button = QPushButton()
        self.send_command_button.setText(language_wrapper.language_word_dict.get("process_input_send_command"))
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.send_command_button)
        self.box_layout.addWidget(self.command_input)
        self.box_layout.addLayout(self.box_h_layout)
        if process_type == "program":
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_program_input_title_label"))
            self.send_command_button.clicked.connect(self.program_send_command)
        elif process_type == "shell":
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_shell_input_title_label"))
            self.send_command_button.clicked.connect(self.shell_send_command)
        else:
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))
            self.send_command_button.clicked.connect(self.debugger_send_command)
            self.main_window.code_difference_result.setCurrentWidget(self.main_window.debugger_result)
        self.setLayout(self.box_layout)

    def debugger_send_command(self):
        if self.main_window.exec_python_debugger is not None:
            process_stdin = self.main_window.exec_python_debugger.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

    def shell_send_command(self):
        if self.main_window.exec_shell is not None:
            process_stdin = self.main_window.exec_shell.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

    def program_send_command(self):
        if self.main_window.exec_program is not None:
            process_stdin = self.main_window.exec_program.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

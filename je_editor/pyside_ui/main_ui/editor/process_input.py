from __future__ import annotations  # 允許未來版本的型別註解功能 / Enable postponed evaluation of type annotations

from typing import \
    TYPE_CHECKING  # 用於避免循環匯入，僅在型別檢查時載入 / Used to avoid circular imports, only loaded during type checking

from PySide6.QtCore import Qt  # Qt 核心模組 / Qt core module
from PySide6.QtWidgets import QWidget, QLineEdit, QBoxLayout, QPushButton, QHBoxLayout

from je_editor.utils.logging.loggin_instance import jeditor_logger

# 匯入 PySide6 的 GUI 元件 / Import GUI widgets from PySide6

# 專案內的日誌紀錄器 / Project's logger instance

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorWidget
    # 僅在型別檢查時匯入 EditorWidget，避免循環依賴 / Import only for type checking to avoid circular dependency

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 多語系支援工具 / Multi-language wrapper for UI text


class ProcessInput(QWidget):
    """
    ProcessInput 是一個輸入視窗，允許使用者輸入指令並傳送到不同的子程序 (program/shell/debugger)。
    ProcessInput is an input widget that allows users to send commands to different subprocesses.
    """

    def __init__(self, main_window: EditorWidget, process_type: str = "debugger"):
        # 初始化時記錄日誌 / Log initialization
        jeditor_logger.info("Init ProcessInput "
                            f"main_window: {main_window} "
                            f"process_type: {process_type}")
        super().__init__()

        # 設定當視窗關閉時自動刪除資源
        # Set attribute to delete widget on close
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # === UI 設定 / UI Setup ===
        self.main_window = main_window  # 儲存主視窗參考 / Store reference to main window
        self.box_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)  # 垂直佈局 / Vertical layout
        self.command_input = QLineEdit()  # 輸入框 / Input field
        self.send_command_button = QPushButton()  # 傳送按鈕 / Send button

        # 設定按鈕文字 (多語系) / Set button text (multi-language)
        self.send_command_button.setText(language_wrapper.language_word_dict.get("process_input_send_command"))

        # 水平佈局，放置按鈕 / Horizontal layout for button
        self.box_h_layout = QHBoxLayout()
        self.box_h_layout.addWidget(self.send_command_button)

        # 將元件加入主佈局 / Add widgets to main layout
        self.box_layout.addWidget(self.command_input)
        self.box_layout.addLayout(self.box_h_layout)

        # 根據 process_type 設定不同的標題與功能 / Configure behavior based on process_type
        if process_type == "program":
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_program_input_title_label"))
            self.send_command_button.clicked.connect(self.program_send_command)
        elif process_type == "shell":
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_shell_input_title_label"))
            self.send_command_button.clicked.connect(self.shell_send_command)
        else:  # 預設為 debugger / Default: debugger
            self.setWindowTitle(language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))
            self.send_command_button.clicked.connect(self.debugger_send_command)
            # 切換主視窗的顯示頁面到 debugger 結果 / Switch main window tab to debugger result
            self.main_window.code_difference_result.setCurrentWidget(self.main_window.debugger_result)

        # 設定主佈局 / Apply layout
        self.setLayout(self.box_layout)

    # === Debugger 指令傳送 / Send command to debugger ===
    def debugger_send_command(self):
        jeditor_logger.info("EditorWidget debugger_send_command")
        if self.main_window.exec_python_debugger is not None:
            process_stdin = self.main_window.exec_python_debugger.process.stdin
            if process_stdin is not None:
                # 將輸入框文字編碼後寫入子程序 stdin / Write encoded input to subprocess stdin
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

    # === Shell 指令傳送 / Send command to shell ===
    def shell_send_command(self):
        jeditor_logger.info("EditorWidget shell_send_command")
        if self.main_window.exec_shell is not None:
            process_stdin = self.main_window.exec_shell.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

    # === Program 指令傳送 / Send command to program ===
    def program_send_command(self):
        jeditor_logger.info("EditorWidget program_send_command")
        if self.main_window.exec_program is not None:
            process_stdin = self.main_window.exec_program.process.stdin
            if process_stdin is not None:
                process_stdin.write(self.command_input.text().encode() + b"\n")
                process_stdin.flush()

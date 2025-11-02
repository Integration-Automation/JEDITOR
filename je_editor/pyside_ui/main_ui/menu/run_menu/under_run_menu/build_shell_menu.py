# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入編輯器元件與輸入處理
# Import EditorWidget and ProcessInput
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.editor.process_input import ProcessInput
# 匯入工具函式：顯示「請先關閉目前執行中的程式」訊息框
# Import utility: show message box if a program is already running
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import please_close_current_running_messagebox
# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入 Qt 動作
# Import QAction
from PySide6.QtGui import QAction

# 匯入 ShellManager，用於執行系統命令
# Import ShellManager for executing shell commands
from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager

# 匯入多語言包裝器
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定 Shell 選單
# Set up the Shell menu
def set_shell_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_shell_menu.py set_shell_menu ui_we_want_to_set: {ui_we_want_to_set}")
    # 在 Run 選單下建立 Shell 子選單
    # Create Shell submenu under Run menu
    ui_we_want_to_set.run_shell_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_on_shell_label"))

    # 建立「在 Shell 執行」動作
    # Add "Run on Shell" action
    ui_we_want_to_set.run_shell_menu.run_on_shell_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_on_shell_label"))
    ui_we_want_to_set.run_shell_menu.run_on_shell_action.triggered.connect(
        lambda: shell_exec(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_shell_menu.addAction(ui_we_want_to_set.run_shell_menu.run_on_shell_action)

    # 建立「顯示 Shell 輸入」動作
    # Add "Show Shell Input" action
    ui_we_want_to_set.run_shell_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_shell_input"))
    ui_we_want_to_set.run_shell_menu.show_shell_input.triggered.connect(
        lambda: show_shell_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_shell_menu.addAction(ui_we_want_to_set.run_shell_menu.show_shell_input)


# 在 Shell 中執行程式碼
# Execute code in Shell
def shell_exec(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_shell_menu.py shell_exec ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        # 確保沒有正在執行的 Shell 程式
        # Ensure no shell process is already running
        if widget.exec_shell is None:
            # 建立 ShellManager 並執行當前編輯器中的程式碼
            # Create ShellManager and execute current editor code
            shell_command = ShellManager(
                main_window=widget,
                shell_encoding=ui_we_want_to_set.encoding)
            shell_command.later_init()
            shell_command.exec_shell(
                widget.code_edit.toPlainText()  # 直接執行編輯器中的文字
            )
            widget.exec_shell = shell_command
        else:
            # 如果已有 Shell 在執行，顯示提示訊息
            # If a shell process is already running, show message
            please_close_current_running_messagebox(ui_we_want_to_set)


# 顯示 Shell 輸入介面
# Show Shell input interface
def show_shell_input(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_shell_menu.py show_shell_input ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.shell_input = ProcessInput(widget, "shell")
        widget.shell_input.show()

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

# 匯入程式執行管理器 (ExecManager)
# Import ExecManager for running/debugging code
from je_editor.pyside_ui.code.code_process.code_exec import ExecManager

# 匯入檔案儲存對話框
# Import file save dialog
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path

# 匯入多語言包裝器
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定 Debug 選單
# Set up the Debug menu
def set_debug_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py set_debug_menu ui_we_want_to_set: {ui_we_want_to_set}")
    # 在 Run 選單下建立 Debug 子選單
    # Create Debug submenu under Run menu
    ui_we_want_to_set.debug_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("editor_debugger_input_title_label"))

    # 建立「執行除錯器」動作
    # Add "Run Debugger" action
    ui_we_want_to_set.debug_menu.run_debugger_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_debugger"))
    ui_we_want_to_set.debug_menu.run_debugger_action.triggered.connect(
        lambda: run_debugger(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.run_debugger_action)

    # 建立「顯示除錯輸入」動作
    # Add "Show Debugger Input" action
    ui_we_want_to_set.debug_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_debugger_input"))
    ui_we_want_to_set.debug_menu.show_shell_input.triggered.connect(
        lambda: show_debugger_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.debug_menu.addAction(ui_we_want_to_set.debug_menu.show_shell_input)


# 執行除錯器 (pdb)
# Run debugger (pdb)
def run_debugger(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py run_debugger ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        # 確保沒有正在執行的除錯器
        # Ensure no debugger is already running
        if widget.exec_python_debugger is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            # 要求使用者選擇儲存檔案路徑
            # Ask user to choose save file path
            if choose_file_get_save_file_path(ui_we_want_to_set):
                # 建立程式執行管理器，並以 pdb 模式執行
                # Create ExecManager and run with pdb
                code_exec = ExecManager(widget, program_encoding=ui_we_want_to_set.encoding)
                code_exec.later_init()
                code_exec.code_result = widget.debugger_result
                code_exec.exec_code(
                    widget.current_file, exec_prefix=["-m", "pdb"]
                )
                # 綁定除錯器與輸入介面
                # Bind debugger and input interface
                widget.exec_python_debugger = code_exec
                widget.debugger_input = ProcessInput(widget)
                widget.debugger_input.show()
        else:
            # 如果已有程式在執行，顯示提示訊息
            # If a program is already running, show message
            please_close_current_running_messagebox(ui_we_want_to_set)


# 顯示除錯輸入介面
# Show debugger input interface
def show_debugger_input(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_debug_menu.py show_debugger_input ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.debugger_input = ProcessInput(widget, "debugger")
        widget.debugger_input.show()
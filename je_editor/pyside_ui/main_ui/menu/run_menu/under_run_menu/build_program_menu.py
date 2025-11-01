# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入 Qt 動作
# Import QAction
from PySide6.QtGui import QAction

# 匯入程式執行管理器 (ExecManager)
# Import ExecManager for running code
from je_editor.pyside_ui.code.code_process.code_exec import ExecManager

# 匯入檔案儲存對話框
# Import file save dialog
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path

# 匯入編輯器元件
# Import EditorWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

# 匯入輸入處理 (用於程式輸入)
# Import ProcessInput for handling program input
from je_editor.pyside_ui.main_ui.editor.process_input import ProcessInput

# 匯入工具函式：顯示「請先關閉目前執行中的程式」訊息框
# Import utility: show message box if a program is already running
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.utils import please_close_current_running_messagebox

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 匯入多語言包裝器
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain


# 設定「執行程式」選單
# Set up the "Run Program" menu
def set_program_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_program_menu.py set_program_menu ui_we_want_to_set: {ui_we_want_to_set}")
    # 在 Run 選單下建立 Program 子選單
    # Create Program submenu under Run menu
    ui_we_want_to_set.run_program_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_program_label"))

    # 建立「執行程式」動作
    # Add "Run Program" action
    ui_we_want_to_set.run_program_menu.run_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_program_label"))
    ui_we_want_to_set.run_program_menu.run_program_action.triggered.connect(
        lambda: run_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_program_menu.addAction(ui_we_want_to_set.run_program_menu.run_program_action)

    # 建立「顯示程式輸入」動作
    # Add "Show Program Input" action
    ui_we_want_to_set.run_program_menu.show_shell_input = QAction(
        language_wrapper.language_word_dict.get("show_program_input"))
    ui_we_want_to_set.run_program_menu.show_shell_input.triggered.connect(
        lambda: show_program_input(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_program_menu.addAction(ui_we_want_to_set.run_program_menu.show_shell_input)


# 執行程式
# Run program
def run_program(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_program_menu.py run_program ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        # 確保沒有正在執行的程式
        # Ensure no program is already running
        if widget.exec_program is None:
            widget.python_compiler = ui_we_want_to_set.python_compiler
            # 要求使用者選擇儲存檔案路徑
            # Ask user to choose save file path
            if choose_file_get_save_file_path(ui_we_want_to_set):
                # 建立程式執行管理器並執行程式
                # Create ExecManager and run program
                code_exec = ExecManager(widget, program_encoding=ui_we_want_to_set.encoding)
                code_exec.later_init()
                code_exec.exec_code(widget.current_file)
                widget.exec_program = code_exec
        else:
            # 如果已有程式在執行，顯示提示訊息
            # If a program is already running, show message
            please_close_current_running_messagebox(ui_we_want_to_set)


# 顯示程式輸入介面
# Show program input interface
def show_program_input(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_program_menu.py show_program_input ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.program_input = ProcessInput(widget, "program")
        widget.program_input.show()
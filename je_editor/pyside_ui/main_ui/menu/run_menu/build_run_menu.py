from __future__ import annotations

from typing import TYPE_CHECKING

# 匯入 Qt 訊息框
# Import QMessageBox for showing dialogs
from PySide6.QtWidgets import QMessageBox

# 匯入執行中程序管理器，用於統一管理所有程式/除錯器/Shell 執行實例
# Import run_instance_manager for managing all running processes
from je_editor.pyside_ui.code.running_process_manager import run_instance_manager

# 匯入編輯器元件
# Import EditorWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

# 匯入子選單建構函式 (Program / Debug / Shell)
# Import submenu builders (Program / Debug / Shell)
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_debug_menu import set_debug_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_program_menu import set_program_menu
from je_editor.pyside_ui.main_ui.menu.run_menu.under_run_menu.build_shell_menu import set_shell_menu

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入 Qt 動作
# Import QAction
from PySide6.QtGui import QAction

# 匯入多語言包裝器
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定 Run 選單
# Set up the Run menu
def set_run_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py set_run_menu ui_we_want_to_set: {ui_we_want_to_set}")
    # 建立 Run 選單
    # Create Run menu
    ui_we_want_to_set.run_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_label"))

    # 加入子選單：Program / Shell / Debug
    # Add submenus: Program / Shell / Debug
    set_program_menu(ui_we_want_to_set)
    set_shell_menu(ui_we_want_to_set)
    set_debug_menu(ui_we_want_to_set)

    # 清除結果
    # Clear execution result
    ui_we_want_to_set.run_menu.clean_result_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_clear_result_label"))
    ui_we_want_to_set.run_menu.clean_result_action.triggered.connect(
        lambda: clean_result(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.clean_result_action)

    # 停止目前程式
    # Stop current program
    ui_we_want_to_set.run_menu.stop_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_stop_program_label"))
    ui_we_want_to_set.run_menu.stop_program_action.triggered.connect(
        lambda: stop_program(ui_we_want_to_set)
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_program_action)

    # 停止所有程式
    # Stop all programs
    ui_we_want_to_set.run_menu.stop_all_program_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_stop_all_program_label"))
    ui_we_want_to_set.run_menu.stop_all_program_action.triggered.connect(
        stop_all_program
    )
    ui_we_want_to_set.run_menu.addAction(ui_we_want_to_set.run_menu.stop_all_program_action)

    # Run 說明子選單
    # Run Help submenu
    ui_we_want_to_set.run_menu.run_help_menu = ui_we_want_to_set.run_menu.addMenu(
        language_wrapper.language_word_dict.get("run_menu_run_help_label"))

    # Run 說明動作
    # Run Help action
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_run_help_label"))
    ui_we_want_to_set.run_menu.run_help_menu.run_help_action.triggered.connect(
        show_run_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.run_help_action)

    # Shell 說明動作
    # Shell Help action
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action = QAction(
        language_wrapper.language_word_dict.get("run_menu_shell_help_label"))
    ui_we_want_to_set.run_menu.run_help_menu.shell_help_action.triggered.connect(
        show_shell_help
    )
    ui_we_want_to_set.run_menu.run_help_menu.addAction(ui_we_want_to_set.run_menu.run_help_menu.shell_help_action)


# 停止目前分頁的程式 / Shell / 除錯器
# Stop current tab's program / shell / debugger
def stop_program(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py stop_program ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        # 停止程式
        if widget.exec_program is not None:
            if widget.exec_program.process is not None:
                widget.exec_program.process.terminate()
            widget.exec_program = None
        # 停止 Shell
        if widget.exec_shell is not None:
            if widget.exec_shell.process is not None:
                widget.exec_shell.process.terminate()
            widget.exec_shell = None
        # 停止除錯器
        if widget.exec_python_debugger is not None:
            if widget.exec_python_debugger.process is not None:
                widget.exec_python_debugger.process.terminate()
            widget.exec_python_debugger = None


# 停止所有執行中的程式
# Stop all running programs
def stop_all_program() -> None:
    jeditor_logger.info("build_run_menu.py stop_all_program")
    run_instance_manager.close_all_instance()


# 清除目前分頁的輸出結果
# Clear current tab's output result
def clean_result(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_run_menu.py clean_result ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.code_result.setPlainText("")


# 顯示 Run 說明
# Show Run help
def show_run_help() -> None:
    jeditor_logger.info("build_run_menu.py show_run_help")
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_run_help_tip")
    )
    message_box.exec()


# 顯示 Shell 說明
# Show Shell help
def show_shell_help() -> None:
    jeditor_logger.info("build_run_menu.py show_shell_help")
    message_box = QMessageBox()
    message_box.setText(
        language_wrapper.language_word_dict.get("run_menu_shell_run_tip")
    )
    message_box.exec()
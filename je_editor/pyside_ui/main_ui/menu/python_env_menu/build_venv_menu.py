# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入顏色設定，用於輸出訊息時的字體顏色
# Import color settings for console/text output
from je_editor.pyside_ui.main_ui.save_settings.user_color_setting_file import actually_color_dict

# 匯入編輯器元件
# Import EditorWidget
from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget

# 匯入使用者設定字典，用來保存 Python 解譯器與環境設定
# Import user settings dictionary for saving Python interpreter and environment settings
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

import os
from pathlib import Path

# 匯入 Qt 動作、快捷鍵、文字格式、訊息框、輸入框、檔案對話框
# Import QAction, QKeySequence, QTextCharFormat, QMessageBox, QInputDialog, QFileDialog
from PySide6.QtGui import QAction, QKeySequence, QTextCharFormat
from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog

# 匯入 ShellManager，用於執行系統命令 (建立 venv、pip install 等)
# Import ShellManager for executing shell commands (create venv, pip install, etc.)
from je_editor.pyside_ui.code.shell_process.shell_exec import ShellManager

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定 Python 環境選單 (venv menu)
# Set up the Python Environment (venv) menu
def set_venv_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py set_venv_menu ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.venv_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("python_env_menu_label"))

    # 建立虛擬環境 (Ctrl+Shift+V)
    # Create virtual environment
    ui_we_want_to_set.venv_menu.change_language_menu = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_create_venv_label"))
    ui_we_want_to_set.venv_menu.change_language_menu.setShortcut(QKeySequence("Ctrl+Shift+V"))
    ui_we_want_to_set.venv_menu.change_language_menu.triggered.connect(
        lambda: create_venv(ui_we_want_to_set))
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.change_language_menu)

    # pip 升級套件 (Ctrl+Shift+U)
    # pip upgrade package
    ui_we_want_to_set.venv_menu.pip_upgrade_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_pip_upgrade_label"))
    ui_we_want_to_set.venv_menu.pip_upgrade_action.setShortcut(QKeySequence("Ctrl+Shift+U"))
    ui_we_want_to_set.venv_menu.pip_upgrade_action.triggered.connect(
        lambda: pip_install_package_update(ui_we_want_to_set))
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_upgrade_action)

    # pip 安裝套件 (Ctrl+Shift+P)
    # pip install package
    ui_we_want_to_set.venv_menu.pip_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_pip_label"))
    ui_we_want_to_set.venv_menu.pip_action.setShortcut(QKeySequence("Ctrl+Shift+P"))
    ui_we_want_to_set.venv_menu.pip_action.triggered.connect(
        lambda: pip_install_package(ui_we_want_to_set))
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.pip_action)

    # 選擇 Python 解譯器
    # Choose Python interpreter
    ui_we_want_to_set.venv_menu.choose_interpreter_action = QAction(
        language_wrapper.language_word_dict.get("python_env_menu_choose_interpreter_label"))
    ui_we_want_to_set.venv_menu.choose_interpreter_action.triggered.connect(
        lambda: chose_python_interpreter(ui_we_want_to_set))
    ui_we_want_to_set.venv_menu.addAction(ui_we_want_to_set.venv_menu.choose_interpreter_action)


# 建立虛擬環境
# Create virtual environment
def create_venv(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py create_venv ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            # 使用 ShellManager 執行 python -m venv venv
            # Use ShellManager to run python -m venv venv
            create_venv_shell = ShellManager(main_window=widget, after_done_function=widget.code_edit.check_env,
                                             shell_encoding=ui_we_want_to_set.encoding)
            create_venv_shell.later_init()
            create_venv_shell.exec_shell([f"{create_venv_shell.compiler_path}", "-m", "venv", "venv"])

            # 在編輯器輸出區顯示訊息
            # Show message in editor output area
            text_cursor = widget.code_result.textCursor()
            text_format = QTextCharFormat()
            text_format.setForeground(actually_color_dict.get("normal_output_color"))
            text_cursor.insertText(language_wrapper.language_word_dict.get("python_env_menu_creating_venv_message"),
                                   text_format)
            text_cursor.insertBlock()
        else:
            # 如果 venv 已存在，顯示提示訊息
            # If venv exists, show message
            message_box = QMessageBox()
            message_box.setText(language_wrapper.language_word_dict.get("python_env_menu_venv_exists"))
            message_box.exec()


# 使用 pip 安裝套件 (通用函式)
# Run pip install command (general function)
def shell_pip_install(ui_we_want_to_set: EditorMain, pip_install_command_list: list):
    jeditor_logger.info("build_venv_menu.py create_venv "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"pip_install_command_list: {pip_install_command_list}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        venv_path = Path(os.getcwd() + "/venv")
        if not venv_path.exists():
            # 如果 venv 不存在，提醒使用者先建立
            # If venv does not exist, remind user to create it first
            message_box = QMessageBox()
            message_box.setText(language_wrapper.language_word_dict.get("python_env_menu_please_create_venv"))
            message_box.exec()
        else:
            # 彈出輸入框，讓使用者輸入套件名稱
            # Ask user to input package name
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_label")
            )
            if press_ok:
                pip_install_shell = ShellManager(main_window=widget, shell_encoding=ui_we_want_to_set.encoding)
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(pip_install_command_list)


# 偵測 venv 是否存在
# Detect if venv exists
def detect_venv() -> bool:
    jeditor_logger.info("build_venv_menu.py detect_venv")
    venv_path = Path(os.getcwd() + "/venv")
    if not venv_path.exists():
        message_box = QMessageBox()
        message_box.setText(language_wrapper.language_word_dict.get("python_env_menu_please_create_venv"))
        message_box.exec()
        return False

# pip 安裝或更新套件
# pip install or update package
def pip_install_package_update(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py pip_install_package_update ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        if detect_venv():
            # 彈出輸入框，讓使用者輸入要安裝或更新的套件名稱
            # Ask user to input package name to install or update
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_or_update_package_messagebox_label")
            )
            if press_ok:
                # 使用 ShellManager 執行 pip install -U
                # Use ShellManager to run pip install -U
                pip_install_shell = ShellManager(
                    main_window=widget,
                    after_done_function=widget.code_edit.check_env,
                    shell_encoding=ui_we_want_to_set.encoding
                )
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}", "-U"]
                )


# pip 安裝套件 (不加 -U)
# pip install package (without -U)
def pip_install_package(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_venv_menu.py pip_install_package ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.python_compiler = ui_we_want_to_set.python_compiler
        # ⚠️ 同樣需要加上 () 呼叫 detect_venv
        # ⚠️ Same here: should be detect_venv()
        if detect_venv():
            # 彈出輸入框，讓使用者輸入要安裝的套件名稱
            # Ask user to input package name
            ask_package_dialog = QInputDialog()
            package_text, press_ok = ask_package_dialog.getText(
                ui_we_want_to_set,
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_title"),
                language_wrapper.language_word_dict.get("python_env_menu_install_package_messagebox_label")
            )
            if press_ok:
                # 使用 ShellManager 執行 pip install
                # Use ShellManager to run pip install
                pip_install_shell = ShellManager(
                    main_window=widget,
                    after_done_function=widget.code_edit.check_env,
                    shell_encoding=ui_we_want_to_set.encoding
                )
                pip_install_shell.later_init()
                pip_install_shell.exec_shell(
                    [f"{pip_install_shell.compiler_path}", "-m", "pip", "install", f"{package_text}"]
                )


# 選擇 Python 解譯器
# Choose Python interpreter
def chose_python_interpreter(ui_we_want_to_set: EditorMain):
    jeditor_logger.info(f"build_venv_menu.py chose_python_interpreter ui_we_want_to_set: {ui_we_want_to_set}")
    file_path = QFileDialog().getOpenFileName(
        parent=ui_we_want_to_set,
        dir=str(Path.cwd())
    )[0]
    if file_path is not None and file_path != "":
        # 更新主程式的 Python 解譯器路徑
        # Update main editor's Python interpreter path
        ui_we_want_to_set.python_compiler = file_path
        # 同時更新使用者設定，讓下次啟動時能記住
        # Update user settings so it persists across sessions
        user_setting_dict.update({"python_compiler": file_path})
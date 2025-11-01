from __future__ import annotations  # 啟用未來版本的型別註解功能 / Enable postponed evaluation of type annotations

from typing import TYPE_CHECKING  # 僅在型別檢查時使用，避免循環匯入 / Used only for type checking to avoid circular imports

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget  # 編輯器分頁元件 / Editor tab widget
from je_editor.utils.logging.loggin_instance import jeditor_logger  # 專案內的日誌紀錄器 / Project logger
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper  # 多語系支援 / Multi-language wrapper

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain  # 僅在型別檢查時匯入 / Import only for type checking

from PySide6.QtGui import QAction, QKeySequence  # Qt 動作與快捷鍵 / Qt actions and shortcuts
from yapf.yapflib.yapf_api import FormatCode  # YAPF 程式碼格式化工具 / YAPF code formatter

from je_editor.utils.json_format.json_process import reformat_json  # JSON 格式化工具 / JSON reformatter


def set_check_menu(ui_we_want_to_set: EditorMain) -> None:
    """
    建立「程式碼檢查/格式化」選單，並加入三個功能：
    - 使用 YAPF 重新格式化 Python 程式碼
    - 重新格式化 JSON
    - 檢查 Python 檔案格式

    Create "Check/Format Code" menu with three actions:
    - Reformat Python code with YAPF
    - Reformat JSON
    - Check Python file format
    """
    jeditor_logger.info(f"build_check_style_menu.py set_check_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # 在主選單中新增一個子選單 / Add submenu to main menu
    ui_we_want_to_set.check_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("check_code_style_menu_label"))

    # === 1. Yapf Python 程式碼格式化 / Yapf Python code reformat ===
    ui_we_want_to_set.check_menu.yapf_check_python_action = QAction(
        language_wrapper.language_word_dict.get("yapf_reformat_label"))
    ui_we_want_to_set.check_menu.yapf_check_python_action.setShortcut(
        QKeySequence("Ctrl+Shift+Y"))  # 設定快捷鍵 / Set shortcut
    ui_we_want_to_set.check_menu.yapf_check_python_action.triggered.connect(
        lambda: yapf_check_python_code(ui_we_want_to_set)
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.yapf_check_python_action)

    # === 2. JSON 重新格式化 / Reformat JSON ===
    ui_we_want_to_set.check_menu.reformat_json_action = QAction(
        language_wrapper.language_word_dict.get("reformat_json_label"))
    ui_we_want_to_set.check_menu.reformat_json_action.setShortcut("Ctrl+j")
    ui_we_want_to_set.check_menu.reformat_json_action.triggered.connect(
        lambda: reformat_json_text(ui_we_want_to_set)
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.reformat_json_action)

    # === 3. Python 格式檢查 / Python format check ===
    ui_we_want_to_set.check_menu.check_python_format = QAction(
        language_wrapper.language_word_dict.get("python_format_checker"))
    ui_we_want_to_set.check_menu.check_python_format.setShortcut("Ctrl+Alt+p")
    ui_we_want_to_set.check_menu.check_python_format.triggered.connect(
        lambda: check_python_format(ui_we_want_to_set)
    )
    ui_we_want_to_set.check_menu.addAction(ui_we_want_to_set.check_menu.check_python_format)


def yapf_check_python_code(ui_we_want_to_set: EditorMain) -> None:
    """
    使用 YAPF 重新格式化目前分頁中的 Python 程式碼
    Reformat current tab's Python code using YAPF
    """
    jeditor_logger.info(f"build_check_style_menu.py yapf_check_python_code ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()  # 取得編輯器文字 / Get code text
        widget.code_result.setPlainText("")  # 清空結果區域 / Clear result area
        format_code = FormatCode(
            unformatted_source=code_text,
            style_config="google"  # 使用 Google 風格 / Use Google style
        )
        if isinstance(format_code, tuple):
            widget.code_edit.setPlainText(format_code[0])  # 將格式化後的程式碼寫回編輯器 / Write formatted code back


def reformat_json_text(ui_we_want_to_set: EditorMain) -> None:
    """
    重新格式化目前分頁中的 JSON 文字
    Reformat JSON text in the current editor tab
    """
    jeditor_logger.info(f"build_check_style_menu.py reformat_json_text ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        code_text = widget.code_edit.toPlainText()
        widget.code_result.setPlainText("")
        widget.code_edit.setPlainText(reformat_json(code_text))  # 呼叫 JSON 格式化工具 / Call JSON reformatter


def check_python_format(ui_we_want_to_set: EditorMain) -> None:
    """
    呼叫 EditorWidget 的檔案格式檢查功能
    Call EditorWidget's file format checker
    """
    jeditor_logger.info(f"build_check_style_menu.py check_python_format ui_we_want_to_set: {ui_we_want_to_set}")
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    if isinstance(widget, EditorWidget):
        widget.check_file_format()
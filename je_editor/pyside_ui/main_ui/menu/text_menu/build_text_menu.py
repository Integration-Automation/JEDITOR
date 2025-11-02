from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 啟用未來註解功能，允許型別提示使用字串前向參照
# Enable future annotations, allowing forward references in type hints
# TYPE_CHECKING 用於避免在執行時載入不必要的模組
# TYPE_CHECKING prevents unnecessary imports at runtime
# 匯入 QAction，用於建立選單動作
# Import QAction for creating menu actions
# 匯入編輯器元件
# Import the Editor widget
# 匯入使用者設定字典，用於儲存字型與字體大小
# Import user setting dictionary to save font and size

# 匯入日誌工具
# Import logger

if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴
    # Import EditorMain only for type checking

from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 匯入多語言包裝器，用於多語系 UI
# Import language wrapper for multilingual UI


def set_text_menu(ui_we_want_to_set: EditorMain):
    """
    建立文字選單，包含字型與字體大小的子選單
    Create the text menu, including font and font size submenus
    """
    jeditor_logger.info(f"build_text_menu.py set_text_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立 Text Menu
    # Create Text Menu
    ui_we_want_to_set.text_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_label"))

    # === 字型選單 (Font Menu) ===
    # === Font Menu ===
    ui_we_want_to_set.text_menu.font_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_label_font"))

    # 將系統支援的字型加入選單
    # Add available system fonts into the menu
    for family in ui_we_want_to_set.font_database.families():
        font_action = QAction(family, parent=ui_we_want_to_set.text_menu.font_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font(ui_we_want_to_set, action))
        ui_we_want_to_set.text_menu.font_menu.addAction(font_action)

    # === 字體大小選單 (Font Size Menu) ===
    # === Font Size Menu ===
    ui_we_want_to_set.text_menu.font_size_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_label_font_size"))

    # 提供 12 ~ 36 pt 的字體大小選項 (每次增加 2)
    # Provide font sizes from 12 to 36 pt (step = 2)
    for size in range(12, 38, 2):
        font_action = QAction(str(size), parent=ui_we_want_to_set.text_menu.font_size_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font_size(ui_we_want_to_set, action))
        ui_we_want_to_set.text_menu.font_size_menu.addAction(font_action)


def set_font(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    """
    設定編輯器的字型
    Set the font family for the editor
    """
    jeditor_logger.info("build_text_menu.py set_font "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")

    # 遍歷所有分頁，找到 EditorWidget 並套用字型
    # Iterate through all tabs, apply font to EditorWidget
    for code_editor in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(code_editor)
        if isinstance(widget, EditorWidget):
            # 設定程式碼編輯區字型
            # Set font for code editor
            widget.code_edit.setStyleSheet(
                f"font-size: {widget.code_edit.font().pointSize()}pt;"
                f"font-family: {action.text()};"
            )
            # 設定輸出結果區字型
            # Set font for result display
            widget.code_result.setStyleSheet(
                f"font-size: {widget.code_result.font().pointSize()}pt;"
                f"font-family: {action.text()};"
            )
            # 更新使用者設定
            # Update user settings
            user_setting_dict.update({"font": action.text()})


def set_font_size(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    """
    設定編輯器的字體大小
    Set the font size for the editor
    """
    jeditor_logger.info("build_text_menu.py set_font_size "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")

    # 遍歷所有分頁，找到 EditorWidget 並套用字體大小
    # Iterate through all tabs, apply font size to EditorWidget
    for code_editor in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(code_editor)
        if type(widget) is EditorWidget:
            # 設定程式碼編輯區字體大小
            # Set font size for code editor
            widget.code_edit.setStyleSheet(
                f"font-size: {int(action.text())}pt;"
                f"font-family: {widget.code_edit.font().family()};"
            )
            # 設定輸出結果區字體大小
            # Set font size for result display
            widget.code_result.setStyleSheet(
                f"font-size: {int(action.text())}pt;"
                f"font-family: {widget.code_result.font().family()};"
            )
            # 更新使用者設定
            # Update user settings
            user_setting_dict.update({"font_size": int(action.text())})

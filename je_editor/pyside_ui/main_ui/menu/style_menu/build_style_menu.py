from __future__ import annotations

from typing import TYPE_CHECKING

# 匯入 Qt 動作
# Import QAction
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

# 匯入使用者設定字典，用來保存 UI 樣式設定
# Import user settings dictionary for saving UI style preferences
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

if TYPE_CHECKING:
    # 僅在型別檢查時匯入 EditorMain，避免循環依賴
    # Import EditorMain only for type checking (avoids circular dependency)
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定 Style 選單
# Set up the Style menu
def set_style_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_style_menu.py set_style_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # 在主選單中新增「Style」子選單
    # Add "Style" submenu under the main menu
    ui_we_want_to_set.menu.style_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("style_menu_label")
    )

    # 預設提供的樣式清單 (深色/淺色不同配色)
    # Predefined style list (dark/light themes with different colors)
    for style in [
        'dark_amber.xml', 'dark_blue.xml', 'dark_cyan.xml', 'dark_lightgreen.xml',
        'dark_pink.xml', 'dark_purple.xml', 'dark_red.xml', 'dark_teal.xml',
        'dark_yellow.xml', 'light_amber.xml', 'light_blue.xml', 'light_cyan.xml',
        'light_cyan_500.xml', 'light_lightgreen.xml', 'light_pink.xml', 'light_purple.xml'
    ]:
        # 建立一個 QAction，名稱為樣式檔名
        # Create an QAction with the style filename as label
        change_style_action = QAction(style, parent=ui_we_want_to_set.menu.style_menu)

        # 綁定觸發事件，呼叫 set_style 來套用樣式
        # Connect action to set_style function
        change_style_action.triggered.connect(
            lambda checked=False, action=change_style_action: set_style(ui_we_want_to_set, action)
        )

        # 將動作加入 Style 選單
        # Add action to the Style menu
        ui_we_want_to_set.menu.style_menu.addAction(change_style_action)

    # 編輯器疊加顯示的開關 / Toggles for the editor's overlays
    ui_we_want_to_set.menu.style_menu.addSeparator()
    add_overlay_toggles(ui_we_want_to_set)


def add_overlay_toggles(ui_we_want_to_set: EditorMain) -> None:
    """
    加入縮排參考線與尾端空白的顯示開關
    Add the toggles for indent guides and trailing-whitespace marking.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    """
    jeditor_logger.info("build_style_menu.py add_overlay_toggles")
    for setting_key, label_key in (
        ("show_indent_guides", "style_menu_indent_guides_label"),
        ("show_trailing_whitespace", "style_menu_trailing_whitespace_label"),
    ):
        toggle = QAction(
            language_wrapper.language_word_dict.get(label_key),
            parent=ui_we_want_to_set.menu.style_menu)
        toggle.setCheckable(True)
        toggle.setChecked(bool(user_setting_dict.get(setting_key, True)))
        toggle.toggled.connect(
            lambda checked, key=setting_key: set_overlay_setting(ui_we_want_to_set, key, checked))
        ui_we_want_to_set.menu.style_menu.addAction(toggle)


def set_overlay_setting(ui_we_want_to_set: EditorMain, setting_key: str, enabled: bool) -> None:
    """
    儲存疊加顯示的開關並立即重畫
    Store an overlay toggle and repaint straight away.

    :param ui_we_want_to_set: 主編輯器視窗 / the main editor window
    :param setting_key: 設定鍵名 / the settings key to update
    :param enabled: 是否顯示 / whether the overlay is shown
    """
    jeditor_logger.info(f"build_style_menu.py set_overlay_setting {setting_key}: {enabled}")
    user_setting_dict.update({setting_key: bool(enabled)})
    tab_widget = getattr(ui_we_want_to_set, "tab_widget", None)
    if tab_widget is None:
        return
    from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
    for index in range(tab_widget.count()):
        widget = tab_widget.widget(index)
        if isinstance(widget, EditorWidget):
            widget.code_edit.viewport().update()


# 套用選擇的樣式
# Apply the selected style
def set_style(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info("build_style_menu.py set_style "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")

    # 呼叫主視窗的 apply_stylesheet 方法，套用選擇的樣式
    # Call main window's apply_stylesheet method to apply the chosen style
    app = QApplication.instance()
    if app is not None:
        ui_we_want_to_set.apply_stylesheet(app, action.text())

    # 更新使用者設定，保存目前選擇的樣式
    # Update user settings dictionary to persist the chosen style
    user_setting_dict.update({"ui_style": action.text()})

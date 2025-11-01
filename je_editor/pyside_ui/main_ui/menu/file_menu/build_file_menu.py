# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 用於型別檢查 (避免循環匯入問題)
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入使用者設定字典，用來保存 UI 設定
# Import user settings dictionary for saving UI preferences
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict

# 匯入 Python 編碼清單 (例如 utf-8, gbk 等)
# Import list of Python encodings (e.g., utf-8, gbk, etc.)
from je_editor.utils.encodings.python_encodings import python_encodings_list

# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入 Qt 動作與字型資料庫
# Import QAction and QFontDatabase from PySide6
from PySide6.QtGui import QAction, QFontDatabase

# 匯入檔案對話框 (新建、開啟、儲存)
# Import file dialogs (create, open, save)
from je_editor.pyside_ui.dialog.file_dialog.create_file_dialog import CreateFileDialog
from je_editor.pyside_ui.dialog.file_dialog.open_file_dialog import choose_file_get_open_file_path, \
    choose_dir_get_dir_path
from je_editor.pyside_ui.dialog.file_dialog.save_file_dialog import choose_file_get_save_file_path


# 設定檔案選單 (File Menu)
# Set up the File menu
def set_file_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_file_menu.py add_dock_widget "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    # 建立 File 選單
    # Create File menu
    ui_we_want_to_set.file_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_label"))

    # 新建檔案動作
    # New File action
    ui_we_want_to_set.file_menu.new_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_new_file_label"))
    ui_we_want_to_set.file_menu.new_file_action.setShortcut("Ctrl+n")
    ui_we_want_to_set.file_menu.new_file_action.triggered.connect(
        lambda: show_create_file_dialog(ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.new_file_action)

    # 開啟檔案動作
    # Open File action
    ui_we_want_to_set.file_menu.open_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_open_file_label"))
    ui_we_want_to_set.file_menu.open_file_action.setShortcut("Ctrl+o")
    ui_we_want_to_set.file_menu.open_file_action.triggered.connect(
        lambda: choose_file_get_open_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_file_action)

    # 開啟資料夾動作
    # Open Folder action
    ui_we_want_to_set.file_menu.open_folder_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_open_folder_label"))
    ui_we_want_to_set.file_menu.open_folder_action.setShortcut("Ctrl+K")
    ui_we_want_to_set.file_menu.open_folder_action.triggered.connect(
        lambda: choose_dir_get_dir_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.open_folder_action)

    # 儲存檔案動作
    # Save File action
    ui_we_want_to_set.file_menu.save_file_action = QAction(
        language_wrapper.language_word_dict.get("file_menu_save_file_label"))
    ui_we_want_to_set.file_menu.save_file_action.setShortcut("Ctrl+s")
    ui_we_want_to_set.file_menu.save_file_action.triggered.connect(
        lambda: choose_file_get_save_file_path(parent_qt_instance=ui_we_want_to_set)
    )
    ui_we_want_to_set.file_menu.addAction(ui_we_want_to_set.file_menu.save_file_action)

    # 加入字型與編碼選單
    # Add font and encoding menus
    add_font_menu(ui_we_want_to_set)
    add_font_size_menu(ui_we_want_to_set)
    add_encoding_menu(ui_we_want_to_set)


# 建立編碼選單
# Add Encoding menu
def add_encoding_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_file_menu.py add_encoding_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.encoding_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_encoding_label"))
    for encoding in python_encodings_list:
        encoding_action = QAction(encoding, parent=ui_we_want_to_set.file_menu.encoding_menu)
        encoding_action.triggered.connect(
            lambda checked=False, action=encoding_action: set_encoding(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.encoding_menu.addAction(encoding_action)


# 設定編碼
# Set encoding
def set_encoding(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info("build_file_menu.py set_encoding "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")
    ui_we_want_to_set.encoding = action.text()
    user_setting_dict.update({"encoding": action.text()})


# 顯示新建檔案對話框
# Show Create File dialog
def show_create_file_dialog(ui_we_want_to_set: EditorMain):
    jeditor_logger.info("build_file_menu.py show_create_file_dialog "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.create_file_dialog = CreateFileDialog()
    ui_we_want_to_set.create_file_dialog.show()


# 建立字型選單
# Add Font menu
def add_font_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_file_menu.py add_font_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.font_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_font_label"))
    for family in QFontDatabase().families():
        font_action = QAction(family, parent=ui_we_want_to_set.file_menu.font_menu)
        font_action.triggered.connect(lambda checked=False, action=font_action: set_font(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.font_menu.addAction(font_action)


# 設定字型
# Set Font
def set_font(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    jeditor_logger.info("build_file_menu.py set_font "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.setStyleSheet(
        f"font-size: {ui_we_want_to_set.font().pointSize()}pt;"
        f"font-family: {action.text()};"
    )
    user_setting_dict.update({"ui_font": action.text()})


# 建立字型大小選單
# Add Font Size menu
def add_font_size_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_file_menu.py add_font_size_menu "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")
    ui_we_want_to_set.file_menu.font_size_menu = ui_we_want_to_set.file_menu.addMenu(
        language_wrapper.language_word_dict.get("file_menu_font_size_label"))
    for size in range(12, 38, 2):  # 12 到 36，每次增加 2
        font_action = QAction(str(size), parent=ui_we_want_to_set.file_menu)
        font_action.triggered.connect(
            lambda checked=False, action=font_action: set_font_size(ui_we_want_to_set, action))
        ui_we_want_to_set.file_menu.font_size_menu.addAction(font_action)


# 設定字型大小
# Set Font Size
def set_font_size(ui_we_want_to_set: EditorMain, action: QAction) -> None:
    # 紀錄日誌，方便除錯與追蹤
    # Log information for debugging and tracking
    jeditor_logger.info("build_file_menu.py set_font_size "
                        f"ui_we_want_to_set: {ui_we_want_to_set} "
                        f"action: {action}")

    # 使用 Qt 的 setStyleSheet 設定整體 UI 的字型樣式
    # Apply stylesheet to set the font size and keep the current font family
    ui_we_want_to_set.setStyleSheet(
        f"font-size: {int(action.text())}pt;"  # 設定字型大小 (pt)
        f"font-family: {ui_we_want_to_set.font().family()};"  # 保持目前的字型家族
    )

    # 更新使用者設定字典，保存字型大小設定
    # Update user settings dictionary to persist font size preference
    user_setting_dict.update({"ui_font_size": int(action.text())})

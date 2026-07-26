# 匯入未來功能，允許延遲型別註解 (Python 3.7+ 常用)
# Import future feature: postponed evaluation of type annotations
from __future__ import annotations

# 僅用於型別檢查，避免循環匯入
# For type checking only (avoids circular imports)
from typing import TYPE_CHECKING

# 匯入 Qt 動作與訊息框
# Import QAction and QMessageBox from PySide6
from PySide6.QtGui import QAction

# 匯入使用者設定字典，用來保存語言設定
# Import user settings dictionary for saving language preferences
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
# 匯入日誌紀錄器
# Import logger instance
from je_editor.utils.logging.loggin_instance import jeditor_logger

# 僅在型別檢查時匯入 EditorMain，避免循環依賴
# Import EditorMain only for type checking (avoids circular dependency)
if TYPE_CHECKING:
    from je_editor.pyside_ui.main_ui.main_editor import EditorMain

# 匯入多語言包裝器，用於 UI 多語言顯示
# Import multi-language wrapper for UI localization
from je_editor.utils.multi_language.multi_language_wrapper import language_wrapper


# 設定語言選單
# Set up the Language menu
def set_language_menu(ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info(f"build_language_server.py set_language_menu ui_we_want_to_set: {ui_we_want_to_set}")

    # 建立 Language 選單
    # Create Language menu
    ui_we_want_to_set.language_menu = ui_we_want_to_set.menu.addMenu(
        language_wrapper.language_word_dict.get("language_menu_label")
    )

    # 每個已註冊的語言各一個項目，名稱以該語言自己的寫法呈現——看不懂目前介面語言
    # 的人才找得到自己的那一個
    # One entry per registered language, each written the way that language writes
    # its own name: someone who cannot read the current interface language still
    # has to be able to find theirs
    ui_we_want_to_set.language_menu.language_actions = {}
    for language in language_wrapper.available_languages():
        action = QAction(
            language_wrapper.display_name(language), ui_we_want_to_set.language_menu)
        action.setCheckable(True)
        action.setChecked(language == language_wrapper.language)
        action.triggered.connect(
            lambda checked=False, name=language: set_language(name, ui_we_want_to_set)
        )
        ui_we_want_to_set.language_menu.addAction(action)
        ui_we_want_to_set.language_menu.language_actions[language] = action

    # 動態加入插件註冊的語言
    # Dynamically add plugin-registered languages
    from je_editor.plugins import get_all_natural_languages
    for lang_key, lang_info in get_all_natural_languages().items():
        if lang_key in ui_we_want_to_set.language_menu.language_actions:
            continue
        display_name = lang_info.get("display_name", lang_key)
        action = QAction(display_name, ui_we_want_to_set.language_menu)
        action.triggered.connect(
            lambda checked=False, lk=lang_key: set_language(lk, ui_we_want_to_set)
        )
        ui_we_want_to_set.language_menu.addAction(action)
        ui_we_want_to_set.language_menu.language_actions[lang_key] = action


# 設定語言
# Set the application language
def set_language(language: str, ui_we_want_to_set: EditorMain) -> None:
    jeditor_logger.info("build_language_server.py set_language "
                        f"language: {language} "
                        f"ui_we_want_to_set: {ui_we_want_to_set}")

    # 先留下舊字典：重新標示畫面時要靠它反查哪些字是翻譯來的
    # Keep the old dictionary: relabelling needs it to tell which words on screen
    # came from a translation and which are file names
    previous_words = dict(language_wrapper.language_word_dict)

    # 重設語言 (更新多語言字典)
    # Reset language (update multi-language dictionary)
    language_wrapper.reset_language(language)

    # 更新使用者設定，保存語言偏好
    # Update user settings dictionary to persist language preference
    user_setting_dict.update({"language": language})

    # 立即重新標示整個介面，不需要重新啟動
    # Relabel the whole interface at once, with no restart
    from je_editor.pyside_ui.main_ui.retranslate import retranslate_ui
    retranslate_ui(ui_we_want_to_set, previous_words)

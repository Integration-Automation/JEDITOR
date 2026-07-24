from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox, QPlainTextEdit

from je_editor.pyside_ui.main_ui.editor.editor_widget import EditorWidget
from je_editor.pyside_ui.main_ui.save_settings.user_setting_file import user_setting_dict
from je_editor.utils.logging.loggin_instance import jeditor_logger
from je_editor.utils.text_stats.text_statistics import TextStatistics, text_statistics

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


def set_text_menu(ui_we_want_to_set: EditorMain) -> None:
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

    ui_we_want_to_set.text_menu.addSeparator()

    # === 自動換行切換 (Word Wrap Toggle) ===
    word_wrap_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_word_wrap"), ui_we_want_to_set)
    word_wrap_action.setCheckable(True)
    word_wrap_action.setChecked(False)
    word_wrap_action.setShortcut("Alt+w")
    word_wrap_action.triggered.connect(
        lambda checked: toggle_word_wrap(ui_we_want_to_set, checked))
    ui_we_want_to_set.text_menu.addAction(word_wrap_action)

    # === 縮排大小選單 (Indent Size Menu) ===
    indent_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_indent_size_menu"))
    for size in (2, 4, 8):
        indent_action = QAction(f"{size} Spaces", parent=indent_menu)
        indent_action.triggered.connect(
            lambda checked=False, s=size: set_indent_size(ui_we_want_to_set, s))
        indent_menu.addAction(indent_action)

    ui_we_want_to_set.text_menu.addSeparator()

    # === 移除行尾空白 (Trim Trailing Whitespace) ===
    trim_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_trim_trailing_whitespace"),
        ui_we_want_to_set)
    trim_action.triggered.connect(lambda: trim_trailing_whitespace(ui_we_want_to_set))
    ui_we_want_to_set.text_menu.addAction(trim_action)

    # === 縮排轉換 (Convert Indentation) ===
    tabs_to_spaces_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_indent_tabs_to_spaces"),
        ui_we_want_to_set)
    tabs_to_spaces_action.triggered.connect(
        lambda: _convert_indentation(ui_we_want_to_set, to_spaces=True))
    ui_we_want_to_set.text_menu.addAction(tabs_to_spaces_action)

    spaces_to_tabs_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_indent_spaces_to_tabs"),
        ui_we_want_to_set)
    spaces_to_tabs_action.triggered.connect(
        lambda: _convert_indentation(ui_we_want_to_set, to_spaces=False))
    ui_we_want_to_set.text_menu.addAction(spaces_to_tabs_action)

    ui_we_want_to_set.text_menu.addSeparator()

    # === 選取行操作 (Selected-line operations) ===
    remove_duplicates_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_remove_duplicate_lines"),
        ui_we_want_to_set)
    remove_duplicates_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "remove_duplicate_selected_lines"))
    ui_we_want_to_set.text_menu.addAction(remove_duplicates_action)

    reverse_lines_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_reverse_lines"),
        ui_we_want_to_set)
    reverse_lines_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "reverse_selected_lines"))
    ui_we_want_to_set.text_menu.addAction(reverse_lines_action)

    natural_sort_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_natural_sort"),
        ui_we_want_to_set)
    natural_sort_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "natural_sort_selected_lines"))
    ui_we_want_to_set.text_menu.addAction(natural_sort_action)

    remove_blank_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_remove_blank_lines"),
        ui_we_want_to_set)
    remove_blank_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "remove_blank_selected_lines"))
    ui_we_want_to_set.text_menu.addAction(remove_blank_action)

    align_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_align_by_delimiter"),
        ui_we_want_to_set)
    align_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "align_selected_lines"))
    ui_we_want_to_set.text_menu.addAction(align_action)

    ui_we_want_to_set.text_menu.addSeparator()

    # === 大小寫轉換 (Case conversion) ===
    uppercase_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_uppercase"), ui_we_want_to_set)
    uppercase_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "uppercase_selection"))
    ui_we_want_to_set.text_menu.addAction(uppercase_action)

    lowercase_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_lowercase"), ui_we_want_to_set)
    lowercase_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "lowercase_selection"))
    ui_we_want_to_set.text_menu.addAction(lowercase_action)

    swapcase_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_swapcase"), ui_we_want_to_set)
    swapcase_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "swapcase_selection"))
    ui_we_want_to_set.text_menu.addAction(swapcase_action)

    titlecase_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_titlecase"), ui_we_want_to_set)
    titlecase_action.triggered.connect(
        lambda: _run_on_editor(ui_we_want_to_set, "titlecase_selection"))
    ui_we_want_to_set.text_menu.addAction(titlecase_action)

    # === 命名風格子選單 (Naming-style submenu) ===
    naming_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_naming_menu"))
    for label_key, method_name in (
        ("text_menu_snake_case", "to_snake_case_selection"),
        ("text_menu_camel_case", "to_camel_case_selection"),
        ("text_menu_pascal_case", "to_pascal_case_selection"),
        ("text_menu_kebab_case", "to_kebab_case_selection"),
    ):
        action = QAction(language_wrapper.language_word_dict.get(label_key), naming_menu)
        action.triggered.connect(
            lambda checked=False, name=method_name: _run_on_editor(ui_we_want_to_set, name))
        naming_menu.addAction(action)

    # === 數字進位子選單 (Number-base submenu) ===
    base_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_number_base_menu"))
    for label_key, method_name in (
        ("text_menu_number_hex", "number_to_hex_selection"),
        ("text_menu_number_decimal", "number_to_decimal_selection"),
        ("text_menu_number_binary", "number_to_binary_selection"),
    ):
        action = QAction(language_wrapper.language_word_dict.get(label_key), base_menu)
        action.triggered.connect(
            lambda checked=False, name=method_name: _run_on_editor(ui_we_want_to_set, name))
        base_menu.addAction(action)

    # === 編碼／解碼子選單 (Encode/Decode submenu) ===
    encode_menu = ui_we_want_to_set.text_menu.addMenu(
        language_wrapper.language_word_dict.get("text_menu_encode_decode_menu"))
    for label_key, method_name in (
        ("text_menu_base64_encode", "base64_encode_selection"),
        ("text_menu_base64_decode", "base64_decode_selection"),
        ("text_menu_url_encode", "url_encode_selection"),
        ("text_menu_url_decode", "url_decode_selection"),
        ("text_menu_html_escape", "html_escape_selection"),
        ("text_menu_html_unescape", "html_unescape_selection"),
        ("text_menu_json_escape", "json_escape_selection"),
        ("text_menu_json_unescape", "json_unescape_selection"),
    ):
        action = QAction(language_wrapper.language_word_dict.get(label_key), encode_menu)
        action.triggered.connect(
            lambda checked=False, name=method_name: _run_on_editor(ui_we_want_to_set, name))
        encode_menu.addAction(action)

    ui_we_want_to_set.text_menu.addSeparator()

    # === 文字統計 (Statistics) ===
    statistics_action = QAction(
        language_wrapper.language_word_dict.get("text_menu_statistics"), ui_we_want_to_set)
    statistics_action.triggered.connect(lambda: show_text_statistics(ui_we_want_to_set))
    ui_we_want_to_set.text_menu.addAction(statistics_action)


def _current_editor(ui_we_want_to_set: EditorMain):
    """取得目前分頁的 EditorWidget / Return the current tab's EditorWidget, or None."""
    widget = ui_we_want_to_set.tab_widget.currentWidget()
    return widget if isinstance(widget, EditorWidget) else None


def _run_on_editor(ui_we_want_to_set: EditorMain, method_name: str) -> None:
    """
    對目前分頁編輯器的 code_edit 呼叫指定方法
    Call a named method on the current editor's code_edit, if there is one.
    """
    jeditor_logger.info(f"build_text_menu.py run_on_editor method: {method_name}")
    widget = _current_editor(ui_we_want_to_set)
    if widget is not None:
        getattr(widget.code_edit, method_name)()


def format_statistics(stats: TextStatistics, scope_label: str) -> str:
    """
    把統計數據組成可顯示的多行字串
    Format statistics into a displayable multi-line string.

    :param stats: 統計數據 / The statistics
    :param scope_label: 範圍描述（整份文件或選取）/ A label for the scope (document or selection)
    :return: 可直接顯示的字串 / A ready-to-show string
    """
    word = language_wrapper.language_word_dict
    return (
        f"{scope_label}\n"
        f"{word.get('text_menu_statistics_lines')}: {stats.lines}\n"
        f"{word.get('text_menu_statistics_words')}: {stats.words}\n"
        f"{word.get('text_menu_statistics_chars')}: {stats.characters}\n"
        f"{word.get('text_menu_statistics_chars_no_spaces')}: {stats.characters_no_spaces}"
    )


def show_text_statistics(ui_we_want_to_set: EditorMain) -> None:
    """
    顯示目前編輯器（選取或整份文件）的文字統計
    Show text statistics for the current editor (selection, or the whole document).
    """
    jeditor_logger.info("build_text_menu.py show_text_statistics")
    widget = _current_editor(ui_we_want_to_set)
    if widget is None:
        return
    cursor = widget.code_edit.textCursor()
    word = language_wrapper.language_word_dict
    if cursor.hasSelection():
        text = cursor.selectedText().replace(" ", "\n")
        scope_label = word.get("text_menu_statistics_scope_selection")
    else:
        text = widget.code_edit.toPlainText()
        scope_label = word.get("text_menu_statistics_scope_document")
    message = format_statistics(text_statistics(text), scope_label)
    QMessageBox.information(
        ui_we_want_to_set, word.get("text_menu_statistics"), message)


def trim_trailing_whitespace(ui_we_want_to_set: EditorMain) -> None:
    """
    對目前分頁的編輯器移除每行行尾空白
    Strip trailing whitespace on the current tab's editor.
    """
    jeditor_logger.info("build_text_menu.py trim_trailing_whitespace")
    widget = _current_editor(ui_we_want_to_set)
    if widget is not None:
        widget.code_edit.trim_trailing_whitespace_document()


def _convert_indentation(ui_we_want_to_set: EditorMain, to_spaces: bool) -> None:
    """
    轉換目前分頁編輯器的縮排（Tab 與空白互轉）
    Convert the current editor's indentation between tabs and spaces.
    """
    jeditor_logger.info(f"build_text_menu.py convert_indentation to_spaces: {to_spaces}")
    widget = _current_editor(ui_we_want_to_set)
    if widget is None:
        return
    indent_size = user_setting_dict.get("indent_size", 4)
    if to_spaces:
        widget.code_edit.convert_indentation_to_spaces(indent_size)
    else:
        widget.code_edit.convert_indentation_to_tabs(indent_size)


def toggle_word_wrap(ui_we_want_to_set: EditorMain, enabled: bool) -> None:
    """
    切換自動換行
    Toggle word wrap for all editor tabs
    """
    jeditor_logger.info(f"build_text_menu.py toggle_word_wrap enabled: {enabled}")
    for i in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(i)
        if isinstance(widget, EditorWidget):
            if enabled:
                widget.code_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            else:
                widget.code_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    user_setting_dict.update({"word_wrap": enabled})


def set_indent_size(ui_we_want_to_set: EditorMain, size: int) -> None:
    """
    設定縮排大小 (空格數)
    Set indent size (number of spaces)
    """
    jeditor_logger.info(f"build_text_menu.py set_indent_size size: {size}")
    from PySide6.QtGui import QFontMetricsF
    for i in range(ui_we_want_to_set.tab_widget.count()):
        widget = ui_we_want_to_set.tab_widget.widget(i)
        if isinstance(widget, EditorWidget):
            widget.code_edit.setTabStopDistance(
                QFontMetricsF(widget.code_edit.font()).horizontalAdvance(" " * size)
            )
    user_setting_dict.update({"indent_size": size})


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
